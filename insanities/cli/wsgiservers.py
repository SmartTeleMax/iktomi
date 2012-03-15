# -*- coding: utf-8 -*-

import sys
import logging
import os
from os import path

logger = logging.getLogger(__name__)


def config_logger(logger=None, name=None, handler=None,
                  level=None, 
                  format='%(asctime)s: %(levelname)-5s: %(name)-15s: %(message)s'):
    if not logger:
        logger = name and logging.getLogger(name) or logging.getLogger()
    level = level or logging.INFO
    logger.setLevel(level)
    handler = handler or logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(format))
    logger.addHandler(handler)
    return logger


def prepare_dir(filename):
    dir = path.dirname(filename)
    if not path.isdir(dir):
        os.makedirs(dir)


def doublefork(pidfile, logfile, cur_dir):
    try:
        if os.fork() > 0:
            sys.exit(0)
    except OSError, e:
        sys.exit('fork #1 failed: (%d) %s\n' % (e.errno, e.strerror))

    os.setsid()
    os.chdir(cur_dir)
    os.umask(002)

    # The second fork _is_ necessary. The first fork accomplishes
    # two things - allow the shell to return, and allow you to do a setsid().
    # The setsid() removes yourself from your controlling terminal.
    # You see, before, you were still listed as a job of your previous process,
    # and therefore the user might accidentally send you a signal.
    # setsid() gives you a new session, and removes the existing controlling terminal.

    # The problem is, you are now a session leader.
    # As a session leader, if you open a file descriptor that is a terminal,
    # it will become your controlling terminal (oops!).
    # Therefore, the second fork makes you NOT be a session leader.
    # Only session leaders can acquire a controlling terminal,
    # so you can open up any file you wish without worrying
    # that it will make you a controlling terminal.

    # So - first fork - allow shell to return, and permit you to call setsid()
    # Second fork - prevent you from accidentally reacquiring a controlling terminal.
    # (taken from aspn.activestate.com)

    try:
        if os.fork() > 0:
            sys.exit(0)
    except OSError, e:
        sys.exit('fork #2 failed: (%d) %s\n' % (e.errno, e.strerror))

    si = open('/dev/null', 'r')
    so = open(logfile, 'a+', 0)

    # Even safer to flush first.
    # Before dup'ing a new file into the underlying stdout/stderr file descriptors,
    # you should flush the stdio buffers.
    # Otherwise, it is entirely possible that pending output could get sent to the wrong file.
    # (taken from aspn.activestate.com)
    sys.stdout.flush()
    sys.stderr.flush()

    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(so.fileno(), sys.stderr.fileno())
    sys.stdout = sys.stderr = so

    fp = open(pidfile, 'w')
    fp.write(str(os.getpid()))
    fp.close()

def daemonize(pidfile, logfile, cur_dir=None):
    cur_dir = cur_dir or path.abspath('.')
    run_dir = path.join(cur_dir, 'run')

    pidfile = pidfile or path.join(run_dir, 'fcgi.pid')
    prepare_dir(pidfile)
    logfile = logfile or path.join(run_dir, 'fcgi.log')
    prepare_dir(logfile)

    if path.isfile(pidfile):
        fp = open(pidfile, 'r')
        pid = int(fp.read())
        fp.close()
        try:
            os.kill(pid, 0)
            print 'process allready running'
            sys.exit(1)
        except OSError, err:
            logger.info('Process allready running: (%d) %s\n' % \
                    (err.errno, err.strerror))
    doublefork(pidfile, logfile, cur_dir)


def flup_fastcgi(wsgi_app, cur_dir=None, bind='', pidfile='', logfile='', 
                 daemon=False, preforked=False, level=None):
    """Run flup fastcgi server at ./run/fcgi.sock"""
    logger = config_logger(level=level)
    if preforked:
        from flup.server import fcgi_fork as fcgi
    else:
        from flup.server import fcgi
    cur_dir = cur_dir or path.abspath('.')
    run_dir = path.join(cur_dir, 'run')
    if ':' in bind:
        host, port = bind.split(':')
        port = int(port)
    else:
        bind = bind or path.join(run_dir, 'fcgi.sock')
        prepare_dir(bind)
    if daemon:
        daemonize(pidfile, logfile, cur_dir)

    logger.info("Starting FastCGI server (flup), current dir '%s'" % cur_dir)
    fcgi.WSGIServer(wsgi_app, bindAddress=bind, umask=777, debug=False).run()
