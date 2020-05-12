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

#
# Constants
#

SLEEP_INTERVAL = 0.1        # FIXME: find a reasonable value
RECURSIVE_MUTEX, SEMAPHORE = list(range(2))
SEM_VALUE_MAX = 2**30

#
# Base class for semaphores and mutexes;
#

class SemLock:

    # KEYS[1] - semaphore counter key
    # KEYS[2] - block list key
    # ARGV[1] - block key
    # return new_value if the semaphore was acquired, 
    # otherwise return the block key
    #
    # Decrements the value by one and returns it if
    # new_value >= 0. Otherwise, puts the block key
    # in the block list so that someone can notify it
    # when it releases the semaphore.
    LUA_ACQUIRE_SCRIPT = """
        local new_value = redis.call('decr', KEYS[1])
        if new_value < 0 then
            redis.call('rpush', KEYS[2], ARGV[1])
            return ARGV[1]
        end
        return new_value
    """

    # KEYS[1] - semaphore counter key
    # KEYS[2] - block list key
    # ARGV[1] - max value
    # return the first block key from the block list
    # referring to the process that was released by
    # this operation. If none was released, 
    # (new_value > 0) then return new_value
    LUA_RELEASE_SCRIPT = """
        local current_value = tonumber(redis.call('get', KEYS[1]))
        if current_value >= tonumber(ARGV[1]) then
            return current_value
        end
        local new_value = redis.call('incr', KEYS[1])
        if new_value < 1 then
            return redis.call('lpop', KEYS[2])
        end
        return new_value
    """

    def __init__(self, value=1, max_value=1):
        self._max_value = max_value
        self._counter_handle = uuid.uuid1().hex
        self._blocked_handle = uuid.uuid1().hex
        self._client = util.get_redis_client()
        self._client.incr(self._counter_handle, value)
        self._register_scripts()

    def _register_scripts(self):
        self._lua_acquire = self._client.register_script(Semaphore.LUA_ACQUIRE_SCRIPT)
        util.make_stateless_script(self._lua_acquire)

        self._lua_release = self._client.register_script(Semaphore.LUA_RELEASE_SCRIPT)
        util.make_stateless_script(self._lua_release)

    def __getstate__(self):
        return (self._max_value, self._counter_handle, self._blocked_handle,
                self._client, self._lua_acquire, self._lua_release)

    def __setstate__(self, state):
        (self._max_value, self._counter_handle, self._blocked_handle,
         self._client, self._lua_acquire, self._lua_release) = state

    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, *args):
        self.release()

    def get_value(self):
        value = self._client.get(self._counter_handle)
        return int(value)

    def acquire(self, block=True):
        keys = [self._counter_handle, self._blocked_handle]
        blocked_key = uuid.uuid1().hex
        res = self._lua_acquire(keys=keys,
                                args=[blocked_key],
                                client=self._client)
        if type(res) == bytes:
            if block:
                self._client.blpop([blocked_key])
                return True
            return False
        return True
        
    def release(self):
        keys = [self._counter_handle, self._blocked_handle]
        res = self._lua_release(keys=keys,
                                args=[self._max_value],
                                client=self._client)
        if type(res) == bytes:
            blocked_key = res.decode()
            self._client.rpush(blocked_key, '') 

    def __repr__(self):
        try:
            value = self.get_value()
        except Exception:
            value = 'unknown'
        return '<%s(value=%s)>' % (self.__class__.__name__, value)

#
# Semaphore
#

class Semaphore(SemLock):

    def __init__(self, value=1):
        super().__init__(value, SEM_VALUE_MAX)

#
# Bounded semaphore
#

class BoundedSemaphore(SemLock):

    def __init__(self, value=1):
        super().__init__(value, value)
        

#
# Non-recursive lock
#

class Lock(SemLock):

    def __init__(self):
        super().__init__(1, 1)
        self.owned = False

    def __setstate__(self, state):
        super().__setstate__(state)
        self.owned = False

    def acquire(self, block=True):
        res = super().acquire(block)
        self.owned = True
        return res

    def release(self):
        super().release()
        self.owned = False

#
# Recursive lock
#

class RLock(Lock):

    def acquire(self, block=True):
        return self.owned or super().acquire(block)


#
# Condition variable
#

class Condition:

    def __init__(self, lock=None):
        if lock:
            self._lock = lock
            self._client = util.get_redis_client()
        else:
            self._lock = Lock()
            # help reducing the amount of open clients
            self._client = self._lock._client
        
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
        assert self._lock.owned

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
        assert self._lock.owned

        wait_handle = self._client.lpop(self._notify_handle)
        if wait_handle is not None:
            res = self._client.rpush(wait_handle, '')

            if not res:
                raise Exception('Condition ({}) could not notify \
                    one waiting process'.format(self._notify_handle))


    def notify_all(self, msg=''):
        assert self._lock.owned

        pipeline = self._client.pipeline(transaction=False)
        pipeline.lrange(self._notify_handle, 0, -1)
        pipeline.delete(self._notify_handle)
        wait_handles, _ = pipeline.execute()

        if len(wait_handles) > 0:
            pipeline = self._client.pipeline(transaction=False)
            for handle in wait_handles:
                pipeline.rpush(handle, msg)
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

#
# Event
#

class Event(object):

    def __init__(self):
        self._cond = Condition()
        self._client = self._cond._client
        self._flag_handle = uuid.uuid1().hex


    def is_set(self):
        return self._client.get(self._flag_handle) == b'1'

    def set(self):
        with self._cond:
            self._client.set(self._flag_handle, '1')
            self._cond.notify_all()

    def clear(self):
        with self._cond:
            self._client.set(self._flag_handle, '0')

    def wait(self, timeout=None):
        with self._cond:
            self._cond.wait_for(self.is_set, timeout)

#
# Barrier
#

class Barrier(threading.Barrier):

    def __init__(self, parties, action=None, timeout=None):
        self._cond = Condition()
        self._client = self._cond._client
        self._state_handle = uuid.uuid1().hex
        self._count_handle = uuid.uuid1().hex
        self._action = action
        self._timeout = timeout
        self._parties = parties
        self._state = 0 #0 filling, 1, draining, -1 resetting, -2 broken
        self._count = 0

    @property
    def _state(self):
        return int(self._client.get(self._state_handle))

    @_state.setter
    def _state(self, value):
        self._client.set(self._state_handle, value)

    @property
    def _count(self):
        return int(self._client.get(self._count_handle))

    @_count.setter
    def _count(self, value):
        self._client.set(self._count_handle, value)
