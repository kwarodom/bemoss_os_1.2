#!/usr/bin/python

"""
Core
"""

import sys
import asyncore
import logging
import signal
import time
import traceback

from task import TaskManager

# some debugging
_log = logging.getLogger(__name__)

# globals
running = False
taskManager = None
deferredFns = []
sleeptime = 0.0

#
#   run
#

SPIN = 1.0

def run(spin=SPIN):
    _log.debug("run spin=%r", spin)
    global running, taskManager, deferredFns, sleeptime

    # reference the task manager (a singleton)
    taskManager = TaskManager()

    # count how many times we are going through the loop
    loopCount = 0

    running = True
    while running:
#       _log.debug("time: %r", time.time())
        loopCount += 1

        # get the next task
        task, delta = taskManager.get_next_task()
        
        try:
            # if there is a task to process, do it
            if task:
                # _log.debug("task: %r", task)
                taskManager.process_task(task)

            # if delta is None, there are no tasks, default to spinning
            if delta is None:
                delta = spin

            # there may be threads around, sleep for a bit
            if sleeptime and (delta > sleeptime):
                time.sleep(sleeptime)
                delta -= sleeptime

            # if there are deferred functions, use a small delta
            if deferredFns:
                delta = min(delta, 0.001)
#           _log.debug("delta: %r", delta)

            # loop for socket activity
            asyncore.loop(timeout=delta, count=1)

            # check for deferred functions
            while deferredFns:
                # get a reference to the list
                fnlist = deferredFns
                deferredFns = []
                
                # call the functions
                for fn, args, kwargs in fnlist:
                    # _log.debug("call: %r %r %r", fn, args, kwargs)
                    fn( *args, **kwargs)
                
                # done with this list
                del fnlist
                
        except KeyboardInterrupt:
            _log.info("keyboard interrupt")
            running = False
        except Exception, e:
            _log.exception("an error has occurred: %s", e)
            
    running = False

#
#   run_once
#

def run_once():
    """
    Make a pass through the scheduled tasks and deferred functions just
    like the run() function but without the asyncore call (so there is no 
    socket IO actviity) and the timers.
    """
    _log.debug("run_once")
    global taskManager, deferredFns

    # reference the task manager (a singleton)
    taskManager = TaskManager()

    try:
        delta = 0.0
        while delta == 0.0:
            # get the next task
            task, delta = taskManager.get_next_task()
            _log.debug("    - task, delta: %r, %r", task, delta)

            # if there is a task to process, do it
            if task:
                taskManager.process_task(task)

            # check for deferred functions
            while deferredFns:
                # get a reference to the list
                fnlist = deferredFns
                deferredFns = []

                # call the functions
                for fn, args, kwargs in fnlist:
                    _log.debug("    - call: %r %r %r", fn, args, kwargs)
                    fn( *args, **kwargs)

                # done with this list
                del fnlist

    except KeyboardInterrupt:
        _log.info("keyboard interrupt")
    except Exception, e:
        _log.exception("an error has occurred: %s", e)

#
#   stop
#

def stop(*args):
    """Call to stop running, may be called with a signum and frame 
    parameter if called as a signal handler."""
    _log.debug("stop")
    global running, taskManager

    if args:
        sys.stderr.write("===== TERM Signal, %s\n" % time.strftime("%d-%b-%Y %H:%M:%S"))
        sys.stderr.flush()

    running = False

    # trigger the task manager event
    if taskManager and taskManager.trigger:
        taskManager.trigger.set()

# set a TERM signal handler
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, stop)

#
#   print_stack
#

def print_stack(sig, frame):
    """Signal handler to print a stack trace and some interesting values."""
    _log.debug("print_stack, %r, %r", sig, frame)
    global running, deferredFns, sleeptime

    sys.stderr.write("==== USR1 Signal, %s\n" % time.strftime("%d-%b-%Y %H:%M:%S"))

    sys.stderr.write("---------- globals\n")
    sys.stderr.write("    running: %r\n" % (running,))
    sys.stderr.write("    deferredFns: %r\n" % (deferredFns,))
    sys.stderr.write("    sleeptime: %r\n" % (sleeptime,))

    sys.stderr.write("---------- stack\n")
    traceback.print_stack(frame)

    # make a list of interesting frames
    flist = []
    f = frame
    while f.f_back:
        flist.append(f)
        f = f.f_back

    # reverse the list so it is in the same order as print_stack
    flist.reverse()
    for f in flist:
        sys.stderr.write("---------- frame: %s\n" % (f,))
        for k, v in f.f_locals.items():
            sys.stderr.write("    %s: %r\n" % (k, v))

    sys.stderr.flush()

# set a USR1 signal handler to print a stack trace
if hasattr(signal, 'SIGUSR1'):
    signal.signal(signal.SIGUSR1, print_stack)

#
#   deferred
#

def deferred(fn, *args, **kwargs):
    # _log.debug("deferred %r %r %r", fn, args, kwargs)
    global deferredFns

    # append it to the list
    deferredFns.append((fn, args, kwargs))

#
#   enable_sleeping
#

def enable_sleeping(stime=0.001):
    _log.debug("enable_sleeping %r", stime)
    global sleeptime

    # set the sleep time
    sleeptime = stime
