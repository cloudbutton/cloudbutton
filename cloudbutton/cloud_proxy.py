import io
import os as base_os
from functools import partial
from .util import get_cloud_storage_client


class CloudFileProxy:
    def __init__(self, cloud_storage=None):
        self._storage = cloud_storage or get_cloud_storage_client()

    def __getattr__(self, name):
        return getattr(base_os, name)

    def listdir(self, path=''):
        if path == '':
            prefix = path
        else:
            prefix = path if path.endswith('/') else path + '/'

        paths = self._storage.list_tmp_data(prefix=prefix)
        names = set()
        for p in paths:
            p = p[len(prefix):] if p.startswith(prefix) else p
            splits = p.split('/')
            name = splits[0] + '/' if len(splits) > 1 else splits[0]
            names |= set([name])
        return names

    def remove(self, key):
        return self._storage.delete_cobject(key=key)


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
    storage = cloud_storage or get_cloud_storage_client()
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
