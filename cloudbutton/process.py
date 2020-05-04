class Process(object):
    '''
    Process objects represent activity that is run in a separate process

    The class is analagous to `threading.Thread`
    '''
    _Popen = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        assert group is None, 'group argument must be None for now'
        count = _current_process._counter.next()
        self._identity = _current_process._identity + (count,)
        self._authkey = _current_process._authkey
        self._daemonic = _current_process._daemonic
        self._tempdir = _current_process._tempdir
        self._parent_pid = os.getpid()
        self._popen = None
        self._target = target
        self._args = tuple(args)
        self._kwargs = dict(kwargs)
        self._name = name or type(self).__name__ + '-' + \
                     ':'.join(str(i) for i in self._identity)

    def run(self):
        '''
        Method to be run in sub-process; can be overridden in sub-class
        '''
        if self._target:
            self._target(*self._args, **self._kwargs)

    def start(self):
        '''
        Start child process
        '''
        assert self._popen is None, 'cannot start a process twice'
        assert self._parent_pid == os.getpid(), \
               'can only start a process object created by current process'
        assert not _current_process._daemonic, \
               'daemonic processes are not allowed to have children'
        _cleanup()
        if self._Popen is not None:
            Popen = self._Popen
        else:
            from .forking import Popen
        self._popen = Popen(self)
        # Avoid a refcycle if the target function holds an indirect
        # reference to the process object (see bpo-30775)
        del self._target, self._args, self._kwargs
        _current_process._children.add(self)

    def terminate(self):
        '''
        Terminate process; sends SIGTERM signal or uses TerminateProcess()
        '''
        self._popen.terminate()

    def join(self, timeout=None):
        '''
        Wait until child process terminates
        '''
        assert self._parent_pid == os.getpid(), 'can only join a child process'
        assert self._popen is not None, 'can only join a started process'
        res = self._popen.wait(timeout)
        if res is not None:
            _current_process._children.discard(self)

    def is_alive(self):
        '''
        Return whether process is alive
        '''
        if self is _current_process:
            return True
        assert self._parent_pid == os.getpid(), 'can only test a child process'

        if self._popen is None:
            return False

        returncode = self._popen.poll()
        if returncode is None:
            return True
        else:
            _current_process._children.discard(self)
            return False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        assert isinstance(name, basestring), 'name must be a string'
        self._name = name

    @property
    def daemon(self):
        '''
        Return whether process is a daemon
        '''
        return self._daemonic

    @daemon.setter
    def daemon(self, daemonic):
        '''
        Set whether process is a daemon
        '''
        assert self._popen is None, 'process has already started'
        self._daemonic = daemonic

    @property
    def authkey(self):
        return self._authkey

    @authkey.setter
    def authkey(self, authkey):
        '''
        Set authorization key of process
        '''
        self._authkey = AuthenticationString(authkey)

    @property
    def exitcode(self):
        '''
        Return exit code of process or `None` if it has yet to stop
        '''
        if self._popen is None:
            return self._popen
        return self._popen.poll()

    @property
    def ident(self):
        '''
        Return identifier (PID) of process or `None` if it has yet to start
        '''
        if self is _current_process:
            return os.getpid()
        else:
            return self._popen and self._popen.pid

    pid = ident

    def __repr__(self):
        if self is _current_process:
            status = 'started'
        elif self._parent_pid != os.getpid():
            status = 'unknown'
        elif self._popen is None:
            status = 'initial'
        else:
            if self._popen.poll() is not None:
                status = self.exitcode
            else:
                status = 'started'

        if type(status) in (int, long):
            if status == 0:
                status = 'stopped'
            else:
                status = 'stopped[%s]' % _exitcode_to_name.get(status, status)

        return '<%s(%s, %s%s)>' % (type(self).__name__, self._name,
                                   status, self._daemonic and ' daemon' or '')

    ##

    def _bootstrap(self):
        from . import util
        global _current_process

        try:
            self._children = set()
            self._counter = itertools.count(1)
            try:
                sys.stdin.close()
                sys.stdin = open(os.devnull)
            except (OSError, ValueError):
                pass
            _current_process = self
            util._finalizer_registry.clear()
            util._run_after_forkers()
            util.info('child process calling self.run()')
            try:
                self.run()
                exitcode = 0
            finally:
                util._exit_function()
        except SystemExit, e:
            if not e.args:
                exitcode = 1
            elif isinstance(e.args[0], (int, long)):
                exitcode = int(e.args[0])
            else:
                sys.stderr.write(str(e.args[0]) + '\n')
                sys.stderr.flush()
                exitcode = 1
        except:
            exitcode = 1
            import traceback
            sys.stderr.write('Process %s:\n' % self.name)
            sys.stderr.flush()
            traceback.print_exc()

        util.info('process exiting with exitcode %d' % exitcode)
        return exitcode
