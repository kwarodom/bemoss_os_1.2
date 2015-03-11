# -*- coding: utf-8 -*-
# Copyright (C)2007 Ingeniweb

"""Recipe cmd"""
from subprocess import check_call
import tempfile
import shutil
import os
import sys
import doctest
from collective.recipe.cmd.compat import execfile


def as_bool(value):
    if value.lower() in ('1', 'true'):
        return True
    return False


def run_commands(cmds, shell):
    cmds = cmds.strip()
    if not cmds:
        return
    if cmds:
        lines = cmds.split('\n')
        lines = [l.strip() for l in lines]
        dirname = tempfile.mkdtemp()
        if sys.platform == 'win32':
            tmpfile = os.path.join(dirname, 'run.bat')
            lines.insert(0, '@echo off')
        else:
            tmpfile = os.path.join(dirname, 'run')
        open(tmpfile, 'w').write('\n'.join(lines))
        if sys.platform == 'win32':
            check_call(tmpfile, shell=True)
        else:
            check_call('%s %s' % (shell, tmpfile), shell=True)
        shutil.rmtree(dirname)


class Cmd(object):

    """This recipe is used by zc.buildout"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        self.on_install = as_bool(options.get('on_install', 'false'))
        self.on_update = as_bool(options.get('on_update', 'false'))
        self.shell = options.get('shell', 'sh')

    def install(self):
        """installer"""
        if self.on_install:
            self.execute()
        return tuple()

    def update(self):
        """updater"""
        if self.on_update:
            self.execute()
        return tuple()

    def execute(self):
        """run the commands
        """
        cmds = self.options.get('cmds', '')
        run_commands(cmds, self.shell)


def uninstallCmd(name, options):
    cmds = options.get('uninstall_cmds', '')
    shell = options.get('shell', 'sh')
    run_commands(cmds, shell)


class Python(Cmd):

    def execute(self):
        """run python code
        """
        cmds = self.options.get('cmds', '')
        cmds = cmds.strip()

        if not cmds:
            return
        if cmds:
            name = self.name
            buildout = self.buildout
            options = self.options
            parser = doctest.DocTestParser()
            lines = [
                line.source for line in parser.parse(cmds) if isinstance(
                    line,
                    doctest.Example)]
            dirname = tempfile.mkdtemp()
            tmpfile = os.path.join(dirname, 'run.py')
            open(tmpfile, 'w').writelines(lines)
            execfile(tmpfile)
            shutil.rmtree(dirname)
