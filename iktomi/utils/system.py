# -*- coding: utf-8 -*-

import os, sys, time, errno


def is_running(pid):
    '''Returns True if process with PID `pid` is running. Current user must
    have permission to access process information.'''
    try:
        os.kill(pid, 0)
    except OSError, exc:
        if exc.errno == errno.ESRCH:
            return False
        raise
    return True


def terminate(pid, sig, timeout):
    '''Terminates process with PID `pid` and returns True if process finished
    during `timeout`. Current user must have permission to access process
    information.'''
    os.kill(pid, sig)
    start = time.time()
    while True:
        if not is_running(pid):
            return True
        if time.time()-start>=timeout:
            return False
        time.sleep(0.1)


def safe_makedirs(*files):
    for filename in files:
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)


def doublefork(pidfile, logfile, cwd, umask):
    '''Daemonize current process.
    After first fork we return to the shell and removing our self from
    controling terminal via `setsid`.
    After second fork we are not session leader any more and cant get
    controlling terminal when opening files.'''
    try:
        if os.fork():
            os._exit(os.EX_OK)
    except OSError, e:
        sys.exit('fork #1 failed: (%d) %s\n' % (e.errno, e.strerror))
    os.setsid()
    os.chdir(cwd)
    os.umask(umask)
    try:
        if os.fork():
            os._exit(os.EX_OK)
    except OSError, e:
        sys.exit('fork #2 failed: (%d) %s\n' % (e.errno, e.strerror))
    si = open('/dev/null')
    so = open(logfile, 'a+', 0)
    os.dup2(si.fileno(), 0)
    os.dup2(so.fileno(), 1)
    os.dup2(so.fileno(), 2)
    sys.stdin = si
    sys.stdout = sys.stderr = so
    with open(pidfile, 'w') as f:
        f.write(str(os.getpid()))
