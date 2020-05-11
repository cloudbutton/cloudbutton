#
# Module implementing synchronization primitives
#
# multiprocessing/synchronize.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

__all__ = [
    'Lock', 'RLock', 'Semaphore', 'BoundedSemaphore', 'Condition', 'Event'
    ]

import threading
import sys
import tempfile
import _multiprocessing
import time
import uuid
from collections import deque
from redis.lock import Lock as RedisLock

from . import context
from . import process
from . import util

# Try to import the mp.synchronize module cleanly, if it fails
# raise ImportError for platforms lacking a working sem_open implementation.
# See issue 3770
try:
    from _multiprocessing import SemLock, sem_unlink
except (ImportError):
    raise ImportError("This platform lacks a functioning sem_open" +
                      " implementation, therefore, the required" +
                      " synchronization primitives needed will not" +
                      " function, see issue 3770.")

#
# Constants
#

SLEEP_INTERVAL = 0.1        # FIXME: find a reasonable value
RECURSIVE_MUTEX, SEMAPHORE = list(range(2))
SEM_VALUE_MAX = _multiprocessing.SemLock.SEM_VALUE_MAX

#
# Base class for semaphores and mutexes; wraps `_multiprocessing.SemLock`
#

class SemLock(object):

    _rand = tempfile._RandomNameSequence()

    def __init__(self, kind, value, maxvalue, *, ctx):
        if ctx is None:
            ctx = context._default_context.get_context()
        name = ctx.get_start_method()
        unlink_now = sys.platform == 'win32' or name == 'fork'
        for i in range(100):
            try:
                sl = self._semlock = _multiprocessing.SemLock(
                    kind, value, maxvalue, self._make_name(),
                    unlink_now)
            except FileExistsError:
                pass
            else:
                break
        else:
            raise FileExistsError('cannot find name for semaphore')

        util.debug('created semlock with handle %s' % sl.handle)
        self._make_methods()

        if sys.platform != 'win32':
            def _after_fork(obj):
                obj._semlock._after_fork()
            util.register_after_fork(self, _after_fork)

        if self._semlock.name is not None:
            # We only get here if we are on Unix with forking
            # disabled.  When the object is garbage collected or the
            # process shuts down we unlink the semaphore name
            from .semaphore_tracker import register
            register(self._semlock.name)
            util.Finalize(self, SemLock._cleanup, (self._semlock.name,),
                          exitpriority=0)

    @staticmethod
    def _cleanup(name):
        from .semaphore_tracker import unregister
        sem_unlink(name)
        unregister(name)

    def _make_methods(self):
        self.acquire = self._semlock.acquire
        self.release = self._semlock.release

    def __enter__(self):
        return self._semlock.__enter__()

    def __exit__(self, *args):
        return self._semlock.__exit__(*args)

    def __getstate__(self):
        context.assert_spawning(self)
        sl = self._semlock
        if sys.platform == 'win32':
            h = context.get_spawning_popen().duplicate_for_child(sl.handle)
        else:
            h = sl.handle
        return (h, sl.kind, sl.maxvalue, sl.name)

    def __setstate__(self, state):
        self._semlock = _multiprocessing.SemLock._rebuild(*state)
        util.debug('recreated blocker with handle %r' % state[0])
        self._make_methods()

    @staticmethod
    def _make_name():
        return '%s-%s' % (process.current_process()._config['semprefix'],
                          next(SemLock._rand))

#
# Semaphore
#

class Semaphore:

    # KEYS[1] - semaphore counter key
    # KEYS[2] - block list key
    # ARGV[1] - block key
    # return 1 if the semaphore was acquired, 
    # otherwise return 0
    LUA_ACQUIRE_SCRIPT = """
        local new_value = redis.call('decr', KEYS[1])
        if new_value < 0 then
            redis.call('rpush', KEYS[2], ARGV[1])
            return 0
        end
        return 1
    """

    # KEYS[1] - semaphore counter key
    # KEYS[2] - block list key
    # return the block key referring to the
    # process that was released by this operation 
    # if none was released, return 0
    LUA_RELEASE_SCRIPT = """
        local new_value = redis.call('incr', KEYS[1])
        if new_value < 1 then
            return redis.call('lpop', KEYS[2])
        end
        return 0
    """

    def __init__(self, value=1):
        self._client = util.get_redis_client()
        self._counter_handle = uuid.uuid1().hex
        self._blocked_handle = uuid.uuid1().hex
        self._client.incr(self._counter_handle, value)
        self._register_scripts()

    def _register_scripts(self):
        self._lua_acquire = self._client.register_script(Semaphore.LUA_ACQUIRE_SCRIPT)
        util.make_stateless_script(self._lua_acquire)

        self._lua_release = self._client.register_script(Semaphore.LUA_RELEASE_SCRIPT)
        util.make_stateless_script(self._lua_release)

    def get_value(self):
        value = self._client.get(self._counter_handle)
        return int(value)

    def acquire(self):
        keys = [self._counter_handle, self._blocked_handle]
        blocked_key = uuid.uuid1().hex
        res = self._lua_acquire(keys=keys,
                                args=[blocked_key],
                                client=self._client)
        if res == 0:
            self._client.blpop([blocked_key])
        
    def release(self):
        keys = [self._counter_handle, self._blocked_handle]
        res = self._lua_release(keys=keys,
                                client=self._client)
        if type(res) == bytes:
            blocked_key = res.decode()
            self._client.rpush(blocked_key, '') 

    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, *args):
        self.release()

    def __repr__(self):
        try:
            value = self.get_value()
        except Exception:
            value = 'unknown'
        return '<%s(value=%s)>' % (self.__class__.__name__, value)

#
# Bounded semaphore
#

class BoundedSemaphore:

    def __init__(self, value=1):
        self._client = util.get_redis_client()
        self._name = uuid.uuid1().hex
        self._limit = value
        self._tokens = deque()

    def acquire(self):
        now = int(time.time() * 1e6)
        token = str(now)
        self._client.zadd(self._name, {token: now})
        self._tokens.append(token)

        rank = self._limit
        while rank >= self._limit:
            rank = self._client.zrank(self._name, token)
            time.sleep(SLEEP_INTERVAL)
            
    def release(self):
        if len(self._tokens) > 0:
            self._client.zrem(self._name, self._tokens.popleft())

    def get_value(self):
        return self._limit - self._client.zcount(self._name, '-inf', 'inf')

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()

    def __repr__(self):
        try:
            value = self.get_value()
        except Exception:
            value = 'unknown'
        return '<%s(value=%s, maxvalue=%s)>' % \
               (self.__class__.__name__, value, self._limit)

#
# Non-recursive lock
#

class Lock(RedisLock):

    def __init__(self):
        redis = util.get_redis_client()
        name = uuid.uuid1().hex
        super().__init__(redis, name, sleep=SLEEP_INTERVAL)

    def get_value(self):
        return 0 if self.locked() else 1

    # def __repr__(self):


#
# Recursive lock
#

class RLock(Lock):

    def acquire(self, *args):
        return super().owned() or super().acquire(*args)

    # def __repr__(self):
    #     try:
    #         if self._semlock._is_mine():
    #             name = process.current_process().name
    #             if threading.current_thread().name != 'MainThread':
    #                 name += '|' + threading.current_thread().name
    #             count = self._semlock._count()
    #         elif self._semlock._get_value() == 1:
    #             name, count = 'None', 0
    #         elif self._semlock._count() > 0:
    #             name, count = 'SomeOtherThread', 'nonzero'
    #         else:
    #             name, count = 'SomeOtherProcess', 'nonzero'
    #     except Exception:
    #         name, count = 'unknown', 'unknown'
    #     return '<%s(%s, %s)>' % (self.__class__.__name__, name, count)

#
# Condition variable
#

class Condition(object):

    def __init__(self, lock=None):
        if lock:
            self._lock = lock
            self._client = util.get_redis_client()
        else:
            self._lock = Lock()
            # help reducing the amount of open connections
            self._client = self._lock.redis
        
        self._notify_handle = uuid.uuid1().hex


    def acquire(self):
        return self._lock.acquire()

    def release(self):
        self._lock.release()

    def __enter__(self):
        return self._lock.__enter__()

    def __exit__(self, *args):
        return self._lock.__exit__(*args)

    def wait(self, timeout=None):
        assert self._lock.owned()

        # Enqueue the key we will be waiting for until we are notified
        self._wait_handle = uuid.uuid1().hex
        res = self._client.rpush(self._notify_handle, self._wait_handle)

        if not res:
            raise Exception('Condition ({}) could not enqueue \
                waiting key'.format(self._notify_handle))

        # Release lock, wait to get notified, acquire lock
        self.release()
        self._client.blpop([self._wait_handle], timeout)
        self.acquire()

    def notify(self):
        assert self._lock.owned()

        wait_handle = self._client.lpop(self._notify_handle)
        if wait_handle is not None:
            res = self._client.rpush(wait_handle, '')

            if not res:
                raise Exception('Condition ({}) could not notify \
                    one waiting process'.format(self._notify_handle))


    def notify_all(self):
        assert self._lock.owned()

        pipeline = self._client.pipeline(transaction=False)
        pipeline.lrange(self._notify_handle, 0, -1)
        pipeline.delete(self._notify_handle)
        wait_handles, _ = pipeline.execute()

        if len(wait_handles) > 0:
            pipeline = self._client.pipeline(transaction=False)
            for handle in wait_handles:
                pipeline.rpush(handle, '')
            results = pipeline.execute()

            if not all(results):
                raise Exception('Condition ({}) could not notify \
                    all waiting processes'.format(self._notify_handle))


    def wait_for(self, predicate, timeout=None):
        result = predicate()
        if result:
            return result
        if timeout is not None:
            endtime = time.monotonic() + timeout
        else:
            endtime = None
            waittime = None
        while not result:
            if endtime is not None:
                waittime = endtime - time.monotonic()
                if waittime <= 0:
                    break
            self.wait(waittime)
            result = predicate()
        return result

    # def __repr__(self):
    #     try:
    #         num_waiters = (self._sleeping_count._semlock._get_value() -
    #                        self._woken_count._semlock._get_value())
    #     except Exception:
    #         num_waiters = 'unknown'
    #     return '<%s(%s, %s)>' % (self.__class__.__name__, self._lock, num_waiters)

#
# Event
#

class Event(object):

    def __init__(self, *, ctx):
        self._cond = ctx.Condition(ctx.Lock())
        self._flag = ctx.Semaphore(0)

    def is_set(self):
        with self._cond:
            if self._flag.acquire(False):
                self._flag.release()
                return True
            return False

    def set(self):
        with self._cond:
            self._flag.acquire(False)
            self._flag.release()
            self._cond.notify_all()

    def clear(self):
        with self._cond:
            self._flag.acquire(False)

    def wait(self, timeout=None):
        with self._cond:
            if self._flag.acquire(False):
                self._flag.release()
            else:
                self._cond.wait(timeout)

            if self._flag.acquire(False):
                self._flag.release()
                return True
            return False

#
# Barrier
#

class Barrier(threading.Barrier):

    def __init__(self, parties, action=None, timeout=None, *, ctx):
        import struct
        from .heap import BufferWrapper
        wrapper = BufferWrapper(struct.calcsize('i') * 2)
        cond = ctx.Condition()
        self.__setstate__((parties, action, timeout, cond, wrapper))
        self._state = 0
        self._count = 0

    def __setstate__(self, state):
        (self._parties, self._action, self._timeout,
         self._cond, self._wrapper) = state
        self._array = self._wrapper.create_memoryview().cast('i')

    def __getstate__(self):
        return (self._parties, self._action, self._timeout,
                self._cond, self._wrapper)

    @property
    def _state(self):
        return self._array[0]

    @_state.setter
    def _state(self, value):
        self._array[0] = value

    @property
    def _count(self):
        return self._array[1]

    @_count.setter
    def _count(self, value):
        self._array[1] = value
