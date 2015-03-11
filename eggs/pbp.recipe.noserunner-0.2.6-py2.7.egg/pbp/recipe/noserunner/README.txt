Supported options
=================

The recipe supports the following options:

eggs
    The eggs option specified a list of eggs to test given as one ore
    more setuptools requirement strings.  Each string must be given on
    a separate line.

script
    The script option gives the name of the script to generate, in the
    buildout bin directory.  Of the option isn't used, the part name
    will be used.

extra-paths
    One or more extra paths to include in the generated test script.

defaults
    The defaults option lets you specify testrunner default
    options. These are specified as Python source for an expression
    yielding a list, typically a list literal.

working-directory
    The working-directory option lets to specify a directory where the
    tests will run. The testrunner will change to this directory when
    run. If the working directory is the empty string or not specified
    at all, the recipe will not change the current working directory.

environment
    A set of environment variables that should be exported before
    starting the tests.

