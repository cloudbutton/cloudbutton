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

    def _refcount(self):
        return int(self._client.get(self._rck))

    def __del__(self):
        refcount = self._decref()
        if refcount <= 0:
            self._client.delete(self._oid, self._rck)

    def __repr__(self):
        return '<%s object, typeid=%r, key=%r, refcount=%r>' % \
               (type(self).__name__, self._typeid, self._oid, self._refcount())

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

    def tolist(self):
        serialized = self._client.lrange(self._oid, 0, -1)
        unserialized = [self._pickler.loads(obj) for obj in serialized]
        return unserialized

class DictProxy(BaseProxy):

    def __init__(self, *args, **kwargs):
        super().__init__('dict')
        self.update(*args, **kwargs)

    def __setitem__(self, k, v):
        serialized = self._pickler.dumps(v)
        self._client.hset(self._oid, k, serialized)

    def __getitem__(self, k):
        serialized = self._client.hget(self._oid, k)
        if serialized is None:
            raise KeyError(k)

        unserialized = self._pickler.loads(serialized)
        return unserialized
        
    def __delitem__(self, k):
        res = self._client.hdel(self._oid, k)   
        if res == 0:
            raise KeyError(k)

    def __contains__(self, k):
        return self._client.hexists(self._oid, k)

    def __len__(self):
        return self._client.hlen(self._oid)

    def __iter__(self):
        return iter(self.keys())

    def get(self, k, default=None):
        try:
            v = self.__getitem__(k)
        except KeyError:
            return default
        else:
            return v

    def pop(self, k, default=None):
        try:
            v = self.__getitem__(k)
        except KeyError:
            return default
        else:
            self.__delitem__(k)
            return v

    def popitem(self):
        try:
            key = self.keys()[0]
            item = (key, self.__getitem__(key))
            self.__delitem__(key)
            return item
        except IndexError:
            raise KeyError('popitem(): dictionary is empty')

    def setdefault(self, k, default=None):
        serialized = self._pickler.dumps(default)
        res = self._client.hsetnx(self._oid, k, serialized)
        if res == 1:
            return default
        else:
            return self.__getitem__(k)

    def update(self, *args, **kwargs):
        items = []
        if args is not ():
            if len(args) > 1:
                raise TypeError('update expected at most'
                    ' 1 arguments, got {}'.format(len(args)))
            try:
                for k in args[0].keys():
                    items.extend((k, self._pickler.dumps(args[0][k])))
            except:
                try:
                    items = []  # just in case
                    for k, v in args[0]:
                        items.extend((k, self._pickler.dumps(v)))
                except:
                    raise TypeError(type(args[0]))

        for k in kwargs.keys():
            items.extend((k, self._pickler.dumps(kwargs[k])))
        self._client.execute_command('HMSET', self._oid, *items)

    def keys(self):
        return [k.decode() for k in self._client.hkeys(self._oid)]

    def values(self):
        return [self._pickler.loads(v) for v in self._client.hvals(self._oid)]

    def items(self):
        raw_dict = self._client.hgetall(self._oid)
        items = []
        for k, v in raw_dict.items():
            items.append((k.decode(), self._pickler.loads(v)))
        return items

    def clear(self):
        self._client.delete(self._oid)

    def copy(self):
        # TODO: use lua script
        return type(self)(self.items())

    def todict(self):
        raw_dict = self._client.hgetall(self._oid)
        py_dict = {}
        for k, v in raw_dict.items():
            py_dict[k.decode()] = self._pickler.loads(v)
        return py_dict


class NamespaceProxy(BaseProxy):
    def __init__(self, **kwargs):
        super().__init__('Namespace')
        DictProxy.update(self, **kwargs)

    def __getattr__(self, k):
        if k[0] == '_':
            return object.__getattribute__(self, k)
        try:
            return DictProxy.__getitem__(self, k)
        except KeyError:
            raise AttributeError(k)

    def __setattr__(self, k, v):
        if k[0] == '_':
            return object.__setattr__(self, k, v)
        DictProxy.__setitem__(self, k, v)

    def __delattr__(self, k):
        if k[0] == '_':
            return object.__delattr__(self, k)
        try:
            return DictProxy.__delitem__(self, k)
        except KeyError:
            raise AttributeError(k)

class ValueProxy(BaseProxy):
    def __init__(self, typecode, value, lock=True):
        super().__init__('Value({})'.format(typecode))
        self.set(value)

    def get(self):
        serialized = self._client.get(self._oid)
        return self._pickler.loads(serialized)

    def set(self, value):
        serialized = self._pickler.dumps(value)
        self._client.set(self._oid, serialized)

    value = property(get, set)

def ArrayProxy(typecode, sequence, lock=True):
    raise NotImplementedError

# ArrayProxy = MakeProxyType('ArrayProxy', (
#     '__len__', '__getitem__', '__setitem__'
#     ))


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
SyncManager.register('Value', ValueProxy)
SyncManager.register('Namespace', NamespaceProxy)
SyncManager.register('Array', ArrayProxy)
