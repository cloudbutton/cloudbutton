#
# Module providing the `SyncManager` class for dealing
# with shared objects
#
# multiprocessing/managers.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

__all__ = [ 'BaseManager', 'SyncManager', 'BaseProxy', 'Token' ]

#
# Imports
#

from . import connection
from . import pool
from . import process
from . import util
from . import synchronize
from . import context
from . import queues
import redis
from copy import deepcopy

pickler = context.reduction.ForkingPickler

#
# Type for identifying shared objects
#

class Token(object):
    '''
    Type to uniquely indentify a shared object
    '''
    __slots__ = ('typeid', 'address', 'id')

    def __init__(self, typeid, address, id):
        (self.typeid, self.address, self.id) = (typeid, address, id)

    def __getstate__(self):
        return (self.typeid, self.address, self.id)

    def __setstate__(self, state):
        (self.typeid, self.address, self.id) = state

    def __repr__(self):
        return '%s(typeid=%r, address=%r, id=%r)' % \
               (self.__class__.__name__, self.typeid, self.address, self.id)


#
# Helper functions
#

def deslice(slic: slice):
    start = slic.start
    end = slic.stop
    step = slic.step

    if start is None:
        start = 0
    if end is None:
        end = -1
    elif start == end or end == 0:
        return None, None, None
    else:
        end -= 1

    return start, end, step


#
# Definition of BaseManager
#

class BaseManager:
    '''
    Base class for managers
    '''
    _registry = {}

    def __init__(self, address=None, authkey=None, serializer='pickle',
                 ctx=None):
        pass

    def get_server(self):
        pass

    def connect(self):
        pass

    def start(self, initializer=None, initargs=()):
        pass

    def _create(self, typeid, *args, **kwds):
        '''
        Create a new shared object; return the token and exposed tuple
        '''
        pass

    def join(self, timeout=None):
        pass

    def _number_of_objects(self):
        '''
        Return the number of shared objects
        '''
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._clean_up()

    def _clean_up(self):
        pass

    @classmethod
    def register(cls, typeid, proxytype=None, callable=None, exposed=None,
                 method_to_typeid=None, create_method=True):
        '''
        Register a typeid with the manager type
        '''
        def temp(self, *args, **kwds):
            util.debug('requesting creation of a shared %r object', typeid)
            proxy = proxytype(*args, **kwds)
            return proxy
        temp.__name__ = typeid
        setattr(cls, typeid, temp)


#
# Definition of BaseProxy
#

class BaseProxy(object):
    '''
    A base for proxies of shared objects
    '''

    def __init__(self, typeid, serializer=None):
        self._typeid = typeid
        # object id
        self._oid = '{}-{}'.format(typeid, util.get_uuid())
        # reference counter key
        self._rck = '{}-{}'.format('ref', self._oid)
        self._pickler = pickler if serializer is None else serializer

        self._client = util.get_redis_client()
        self._incref()

    def __getstate__(self):
        return (self._typeid, self._oid, self._rck,
         self._pickler, self._client)

    def __setstate__(self, state):
        (self._typeid, self._oid, self._rck,
        self._pickler, self._client) = state
        self._incref()

    def _getvalue(self):
        '''
        Get a copy of the value of the referent
        '''
        pass

    def _incref(self):
        return int(self._client.incr(self._rck, 1))

    def _decref(self):
        return int(self._client.decr(self._rck, 1))

    def refcount(self):
        return int(self._client.get(self._rck))

    def __del__(self):
        refcount = self._decref()
        if refcount <= 0:
            self._client.delete(self._oid, self._rck)

    def __repr__(self):
        return '<%s object, typeid=%r, key=%r, refcount=%r>' % \
               (type(self).__name__, self._typeid, self._oid, self.refcount())

    def __str__(self):
        '''
        Return representation of the referent (or a fall-back if that fails)
        '''
        return repr(self)


#
# Types/callables which we will register with SyncManager
#

class ListProxy(BaseProxy):

    # KEYS[1] - key to extend
    # KEYS[2] - key to extend with
    # ARGV[1] - number of repetitions
    # A = A + B * C
    LUA_EXTEND_LIST_SCRIPT = """
        local values = redis.call('LRANGE', KEYS[2], 0, -1)
        if #values == 0 then
            return
        else
            for i=1,tonumber(ARGV[1]) do
                redis.call('RPUSH', KEYS[1], unpack(values))
            end
        end
    """

    def __init__(self, iterable=None, serializer=None):
        super().__init__('list', serializer)
        self._lua_extend_list = self._client.register_script(ListProxy.LUA_EXTEND_LIST_SCRIPT)
        util.make_stateless_script(self._lua_extend_list)

        if iterable is not None:
            self.extend(iterable)

    def __getstate__(self):
        return super().__getstate__() + (self._lua_extend_list,)

    def __setstate__(self, state):
        super().__setstate__(state[:-1])
        self._lua_extend_list = state[-1]

    def __setitem__(self, i, obj):
        if isinstance(i, int) or hasattr(i, '__index__'):
            idx = i.__index__()
            serialized = self._pickler.dumps(obj)
            try:
                self._client.lset(self._oid, idx, serialized)
            except redis.exceptions.ResponseError:
                # raised when index >= len(self)
                raise IndexError('list assignment index out of range')

        elif isinstance(i, slice):    # TODO: step
            start, end, step = deslice(i)
            if start is None:
                return

            pipeline = self._client.pipeline(transaction=False)
            try:
                iterable = iter(obj)
                for j in range(start, end):
                    obj = next(iterable)
                    serialized = self._pickler.dumps(obj)
                    pipeline.lset(self._oid, j, serialized)
            except StopIteration:
                pass
            except redis.exceptions.ResponseError:
                # raised when index >= len(self)
                pipeline.execute()
                self.extend(iterable)
                return
            except TypeError:
                raise TypeError('can only assign an iterable')
            pipeline.execute()
        else:    
            raise TypeError('list indices must be integers '
                'or slices, not {}'.format(type(i)))

    def __getitem__(self, i):
        if isinstance(i, int) or hasattr(i, '__index__'):
            idx = i.__index__()
            serialized = self._client.lindex(self._oid, idx)
            if serialized is not None:
                return self._pickler.loads(serialized)
            raise IndexError('list index out of range')

        elif isinstance(i, slice):    # TODO: step
            start, end, step = deslice(i)
            if start is None:
                return []
            serialized = self._client.lrange(self._oid, start, end)
            unserialized = [self._pickler.loads(obj) for obj in serialized]
            #return unserialized
            return type(self)(unserialized, self._pickler)
        else:
            raise TypeError('list indices must be integers '
                'or slices, not {}'.format(type(i)))

    def extend(self, iterable):
        if isinstance(iterable, type(self)):
            self._extend_same_type(iterable, 1)
        else:
            if iterable != []:
                values = map(self._pickler.dumps, iterable)
                self._client.rpush(self._oid, *values)

    def _extend_same_type(self, listproxy, repeat=1):
        self._lua_extend_list(keys=[self._oid, listproxy._oid],
                              args=[repeat],
                              client=self._client)

    def append(self, obj):
        serialized = self._pickler.dumps(obj)
        self._client.rpush(self._oid, serialized)

    def pop(self, index=None):
        if index is None:
            serialized = self._client.rpop(self._oid)
            if serialized is not None:
                return self._pickler.loads(serialized)
        else:
            raise NotImplementedError

    def __deepcopy__(self, memo):
        selfcopy = type(self)(serializer=self._pickler)

        # We should test the DUMP/RESTORE strategy 
        # although it has serialization costs
        selfcopy._extend_same_type(self)

        memo[id(self)] = selfcopy
        return selfcopy

    def __add__(self, x):
        # FIXME: list only allows concatenation to other list objects
        #        (altough it can to be extended by iterables)
        newlist = deepcopy(self)
        return newlist.__iadd__(x)

    def __iadd__(self, x):
        # FIXME: list only allows concatenation to other list objects
        #        (altough it can to be extended by iterables)
        self.extend(x)
        return self       

    def __mul__(self, n):
        if not isinstance(n, int):
            raise TypeError("TypeError: can't multiply sequence"
                    " by non-int of type {}". format(type(n)))
        if n < 1:
            return type(self)(serializer=self._pickler) # FIXME: return [] ?
        else:
            newlist = type(self)(serializer=self._pickler)
            newlist._extend_same_type(self, repeat=n)
            return newlist

    def __rmul__(self, n):
        if not isinstance(n, int):
            raise TypeError("TypeError: can't multiply sequence"
                    " by non-int of type {}". format(type(n)))
        return self.__mul__(n)

    def __imul__(self, n):
        if not isinstance(n, int):
            raise TypeError("TypeError: can't multiply sequence"
                    " by non-int of type {}". format(type(n)))
        if n > 1:
            self._extend_same_type(self, repeat=n-1)
        return self

    def __len__(self):
        return self._client.llen(self._oid)

    def remove(self, obj):
        serialized = self._pickler.dumps(obj)
        self._client.lrem(self._oid, 1, serialized)
        return self

    def reverse(self):
        length = len(self)
        rev = reversed(self)
        self.extend(rev)
        self._client.ltrim(self._oid, length, -1)
        return self

    def sort(self, key=None, reverse=False):
        length = len(self)
        sortd = sorted(self, key=key, reverse=reverse)
        self.extend(sortd)
        self._client.ltrim(self._oid, length, -1)
        return self

    def __delitem__(self, i):
        raise NotImplementedError
    
    def index(self, obj, start=0, end=-1):
        raise NotImplementedError
        
    def count(self, obj):
        raise NotImplementedError

    def insert(self, index, obj):
        raise NotImplementedError


class DictProxy(BaseProxy):
    pass

# DictProxy = MakeProxyType('DictProxy', (
#     '__contains__', '__delitem__', '__getitem__', '__iter__', '__len__',
#     '__setitem__', 'clear', 'copy', 'get', 'has_key', 'items',
#     'keys', 'pop', 'popitem', 'setdefault', 'update', 'values'
#     ))
# DictProxy._method_to_typeid_ = {
#     '__iter__': 'Iterator',
#     }


class Namespace(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    def __repr__(self):
        items = list(self.__dict__.items())
        temp = []
        for name, value in items:
            if not name.startswith('_'):
                temp.append('%s=%r' % (name, value))
        temp.sort()
        return '%s(%s)' % (self.__class__.__name__, ', '.join(temp))

class Value(object):
    def __init__(self, typecode, value, lock=True):
        self._typecode = typecode
        self._value = value
    def get(self):
        return self._value
    def set(self, value):
        self._value = value
    def __repr__(self):
        return '%s(%r, %r)'%(type(self).__name__, self._typecode, self._value)
    value = property(get, set)

def Array(typecode, sequence, lock=True):
    return array.array(typecode, sequence)

#
# Proxy types used by SyncManager
#

class IteratorProxy(BaseProxy):
    _exposed_ = ('__next__', 'send', 'throw', 'close')
    def __iter__(self):
        return self
    def __next__(self, *args):
        return self._callmethod('__next__', args)
    def send(self, *args):
        return self._callmethod('send', args)
    def throw(self, *args):
        return self._callmethod('throw', args)
    def close(self, *args):
        return self._callmethod('close', args)


class NamespaceProxy(BaseProxy):
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__')
    def __getattr__(self, key):
        if key[0] == '_':
            return object.__getattribute__(self, key)
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('__getattribute__', (key,))
    def __setattr__(self, key, value):
        if key[0] == '_':
            return object.__setattr__(self, key, value)
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('__setattr__', (key, value))
    def __delattr__(self, key):
        if key[0] == '_':
            return object.__delattr__(self, key)
        callmethod = object.__getattribute__(self, '_callmethod')
        return callmethod('__delattr__', (key,))


class ValueProxy(BaseProxy):
    _exposed_ = ('get', 'set')
    def get(self):
        return self._callmethod('get')
    def set(self, value):
        return self._callmethod('set', (value,))
    value = property(get, set)


# BaseListProxy = MakeProxyType('BaseListProxy', (
#     '__add__', '__contains__', '__delitem__', '__getitem__', '__len__',
#     '__mul__', '__reversed__', '__rmul__', '__setitem__',
#     'append', 'count', 'extend', 'index', 'insert', 'pop', 'remove',
#     'reverse', 'sort', '__imul__'
#     ))
# class ListProxy(BaseListProxy):
#     def __iadd__(self, value):
#         self._callmethod('extend', (value,))
#         return self
#     def __imul__(self, value):
#         self._callmethod('__imul__', (value,))
#         return self


# DictProxy = MakeProxyType('DictProxy', (
#     '__contains__', '__delitem__', '__getitem__', '__iter__', '__len__',
#     '__setitem__', 'clear', 'copy', 'get', 'has_key', 'items',
#     'keys', 'pop', 'popitem', 'setdefault', 'update', 'values'
#     ))
# DictProxy._method_to_typeid_ = {
#     '__iter__': 'Iterator',
#     }


# ArrayProxy = MakeProxyType('ArrayProxy', (
#     '__len__', '__getitem__', '__setitem__'
#     ))


# BasePoolProxy = MakeProxyType('PoolProxy', (
#     'apply', 'apply_async', 'close', 'imap', 'imap_unordered', 'join',
#     'map', 'map_async', 'starmap', 'starmap_async', 'terminate',
#     ))
# BasePoolProxy._method_to_typeid_ = {
#     'apply_async': 'AsyncResult',
#     'map_async': 'AsyncResult',
#     'starmap_async': 'AsyncResult',
#     'imap': 'Iterator',
#     'imap_unordered': 'Iterator'
#     }
# class PoolProxy(BasePoolProxy):
#     def __enter__(self):
#         return self
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.terminate()

#
# Definition of SyncManager
#

class SyncManager(BaseManager):
    '''
    Subclass of `BaseManager` which supports a number of shared object types.

    The types registered are those intended for the synchronization
    of threads, plus `dict`, `list` and `Namespace`.

    The `multiprocessing.Manager()` function creates started instances of
    this class.
    '''

SyncManager.register('Queue', queues.Queue)
SyncManager.register('JoinableQueue', queues.JoinableQueue)
SyncManager.register('SimpleQueue', queues.SimpleQueue)
SyncManager.register('Event', synchronize.Event)
SyncManager.register('Lock', synchronize.Lock)
SyncManager.register('RLock', synchronize.RLock)
SyncManager.register('Semaphore', synchronize.Semaphore)
SyncManager.register('BoundedSemaphore', synchronize.BoundedSemaphore)
SyncManager.register('Condition', synchronize.Condition)
SyncManager.register('Barrier', synchronize.Barrier)
SyncManager.register('Pool', pool.Pool)
SyncManager.register('list', ListProxy)
SyncManager.register('dict', DictProxy)
# SyncManager.register('Value', Value, ValueProxy)
# SyncManager.register('Array', Array, ArrayProxy)
# SyncManager.register('Namespace', Namespace, NamespaceProxy)

# # types returned by methods of PoolProxy
# SyncManager.register('Iterator', proxytype=IteratorProxy, create_method=False)
# SyncManager.register('AsyncResult', create_method=False)
