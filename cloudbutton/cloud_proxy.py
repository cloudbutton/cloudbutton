import io
import os as base_os
from . import get_context
from functools import partial


class CloudFileProxy:
    def __init__(self, ctx=None):
        # Use context storage because it is lazily created
        # the first time it is used, and not when importing the module
        self._ctx = ctx or get_context()

    def __getattr__(self, name):
        return getattr(base_os, name)

    def listdir(self, path=''):
        storage = self._ctx._storage

        if path == '':
            prefix = path
        else:
            prefix = path if path.endswith('/') else path + '/'

        paths = storage.list_tmp_data(prefix=prefix)
        names = set()
        for p in paths:
            p = p[len(prefix):] if p.startswith(prefix) else p
            splits = p.split('/')
            name = splits[0] + '/' if len(splits) > 1 else splits[0]
            names |= set([name])
        return names

    def remove(self, key):
        storage = self._ctx._storage
        return storage.delete_cobject(key=key)


class DelayedBytesBuffer(io.BytesIO):
    def __init__(self, action, initial_bytes=None):
        super().__init__(initial_bytes)
        self._action = action

    def close(self):
        self._action(self.getvalue())
        io.BytesIO.close(self)


class DelayedStringBuffer(io.StringIO):
    def __init__(self, action, initial_value=None):
        super().__init__(initial_value)
        self._action = action
        
    def close(self):
        self._action(self.getvalue())
        io.StringIO.close(self)


def cloud_open(filename, mode='r', cloud_storage=None):
    storage = cloud_storage or get_context()._storage
    if 'r' in mode:
        if 'b' in mode:
            # we could get_data(stream=True) but some streams are not seekable
            return io.BytesIO(storage.get_data(filename))
        else:
            return io.StringIO(storage.get_data(filename).decode())

    if 'w' in mode:
        action = partial(storage.put_data, filename)
        if 'b' in mode:
            return DelayedBytesBuffer(action)
        else:
            return DelayedStringBuffer(action)


def CloudStorage(self, config=None):
    from .util import get_cloud_storage_client
    return get_cloud_storage_client(config)

@property
def os(self):
    try:
        return self._proxy
    except AttributeError:
        from .cloud_proxy import CloudFileProxy
        self._proxy = CloudFileProxy(ctx=self.get_context())
        return self._proxy

def open(self, *args, **kwargs):
    try:
        kwargs['cloud_storage'] = self._storage
        return self._open(*args, **kwargs)
    except AttributeError:
        # Could be an actual AttributeError
        if hasattr(self, '_open'):
            raise
        else:          
            from .cloud_proxy import cloud_open 
            self._open = cloud_open
            kwargs['cloud_storage'] = self._storage
            return self._open(*args, **kwargs)

@property
def _storage(self):
    # lazily created because we don't know if
    # we will use it or if we have the config for it
    try:
        return self._lazy_storage
    except AttributeError:
        self._lazy_storage = self.CloudStorage()
        return self._lazy_storage
