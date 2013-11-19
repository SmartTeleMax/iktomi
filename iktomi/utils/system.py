# -*- coding: utf-8 -*-

import os
import sys


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
    sys.stdin.close()
    os.dup2(si.fileno(), 0)
    sys.stdout.close()
    os.dup2(so.fileno(), 1)
    sys.stderr.close()
    os.dup2(so.fileno(), 2)
    sys.stdin = si
    sys.stdout = sys.stderr = so
    with open(pidfile, 'w') as f:
        f.write(str(os.getpid()))
