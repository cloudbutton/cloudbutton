import io
import os as base_os
from .util import get_cloud_storage_client

class CloudOpenFile:
    def __init__(self, filename, mode='w', cloud_storage=None):
        self.cs = cloud_storage or get_cloud_storage_client()
        self.key = filename
        self.buf = None
        if 'r' in mode:
            self.buf = io.BytesIO(self.cs.get_data(self.key))

    def __enter__(self):
        if self.buf is None:
            return self
        else:
            return self.buf

    def __exit__(self, *args):
        self.key = None
        if self.buf is not None:
            try:
                self.buf.close()
            except:
                pass

    def write(self, data):
        self.cs.put_data(self.key, data)

    def read(self, x):
        return self.buf.read(x)

class CloudFileProxy:
    def __init__(self, cloud_storage=None):
        self.cs = cloud_storage or get_cloud_storage_client()

    def __getattr__(self, name):
        return getattr(base_os, name)
        
    def open(self, filename, mode='r'):
        if 'r' in mode:
            return io.BytesIO(self.cs.get_data(filename))
        return CloudOpenFile(filename, mode, self.cs)

    def listdir(self, path):
        return [base_os.path.basename(name) for name in self.cs.list_tmp_data(prefix=path)]

    def remove(self, key):
        return self.cs.delete_cobject(key=key)
