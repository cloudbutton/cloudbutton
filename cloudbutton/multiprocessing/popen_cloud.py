import pywren_ibm_cloud as pywren
from pywren_ibm_cloud.wait import ALL_COMPLETED, ANY_COMPLETED, ALWAYS

from . import util

__all__ = ['Popen']


#
# Start child process using cloud
#

class Popen(object):
    method = 'cloud'

    def __init__(self, process_obj):
        util._flush_std_streams()
        self.returncode = None
        self._executor = pywren.function_executor()
        self._launch(process_obj)

    def duplicate_for_child(self, fd):
        return fd

    def poll(self, flag=ALWAYS):
        if self.returncode is None:
            self._executor.wait([self.sentinel], return_when=flag)
            if self.sentinel.ready or self.sentinel.done:
                self.returncode = 0
            if self.sentinel.error:
                self.returncode = 1
        return self.returncode

    def wait(self, timeout=None):
        if self.returncode is None:
            wait = self._executor.wait
            if not wait([self.sentinel], timeout=timeout):
                return None
            # This shouldn't block if wait() returned successfully.
            return self.poll(ALWAYS if timeout == 0.0 else ALL_COMPLETED)
        return self.returncode

    def terminate(self):
        if self.returncode is None:
            try:
                self.sentinel.cancel()
            except NotImplementedError:
                pass

    def _launch(self, process_obj):
        fn_args = [*process_obj._args, *process_obj._kwargs]
        self.sentinel = self._executor.call_async(process_obj._target, fn_args)
