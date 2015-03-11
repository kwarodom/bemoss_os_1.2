# -*- coding: utf-8 -*-
"""
Doctest runner for 'collective.recipe.cmd'.
"""
__docformat__ = 'restructuredtext'

import os
import sys
import unittest
import zc.buildout.tests
import zc.buildout.testing

from zope.testing import doctest, renormalizing

optionflags = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_ONLY_FIRST_FAILURE)


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)

    # Install the recipe in develop mode
    zc.buildout.testing.install_develop('collective.recipe.cmd', test)

    test.globs['os'] = os
    test.globs['sys'] = sys
    test.globs['test_dir'] = os.path.dirname(__file__)


def test_suite():
    suite = unittest.TestSuite((
        doctest.DocFileSuite(
            '../../../../README.rst',
            setUp=setUp,
            tearDown=zc.buildout.testing.buildoutTearDown,
            optionflags=optionflags,
            checker=renormalizing.RENormalizing([
                # If want to clean up the doctest output you
                # can register additional regexp normalizers
                # here. The format is a two-tuple with the RE
                # as the first item and the replacement as the
                # second item, e.g.
                # (re.compile('my-[rR]eg[eE]ps'), 'my-regexps')
                zc.buildout.testing.normalize_path,
            ]),
        ),
    ))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
