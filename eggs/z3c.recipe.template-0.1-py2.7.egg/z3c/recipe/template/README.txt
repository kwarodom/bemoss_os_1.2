Detailed Description
********************

Simple creation of a file out of a template
===========================================

Lets create a minimal `buildout.cfg` file::

  >>> write('buildout.cfg',
  ... '''
  ... [buildout]
  ... parts = template
  ... offline = true
  ...
  ... [template]
  ... recipe = z3c.recipe.template
  ... input = template.in
  ... output = template
  ... ''')

We create a template file::

  >>> write('template.in',
  ... '''#
  ... My template knows about buildout path:
  ...   ${buildout:directory}
  ... ''')

Now we can run buildout::

  >>> print system(join('bin', 'buildout')),
  Installing template.

The template was indeed created::

  >>> cat('template')
  #
  My template knows about buildout path:
  .../sample-buildout

The variable ``buildout:directory`` was also substituted by a path.


Creating a template in a variable path
======================================

Lets create a minimal `buildout.cfg` file. This time the output should
happen in a variable path::

  >>> write('buildout.cfg',
  ... '''
  ... [buildout]
  ... parts = template
  ... offline = true
  ...
  ... [template]
  ... recipe = z3c.recipe.template
  ... input = template.in
  ... output = ${buildout:parts-directory}/template
  ... ''')

Now we can run buildout::

  >>> print system(join('bin', 'buildout')),
  Uninstalling template.
  Installing template.

The template was indeed created::

  >>> cat('parts', 'template')
  #
  My template knows about buildout path:
  .../sample-buildout


Creating missing paths
======================

If an output file should be created in a path that does not yet exist,
then the missing items will be created for us::

  >>> write('buildout.cfg',
  ... '''
  ... [buildout]
  ... parts = template
  ... offline = true
  ...
  ... [template]
  ... recipe = z3c.recipe.template
  ... input = template.in
  ... output = ${buildout:parts-directory}/etc/template
  ... ''')

  >>> print system(join('bin', 'buildout')),
  Uninstalling template.
  Installing template.

Also creation of several subdirectories is supported::


  >>> write('buildout.cfg',
  ... '''
  ... [buildout]
  ... parts = template
  ... offline = true
  ...
  ... [template]
  ... recipe = z3c.recipe.template
  ... input = template.in
  ... output = ${buildout:parts-directory}/foo/bar/template
  ... ''')

  >>> print system(join('bin', 'buildout')),
  Uninstalling template.
  Installing template.

  >>> cat('parts', 'foo', 'bar', 'template')
  #
  My template knows about buildout path:
  .../sample-buildout

When changes happen to the output path, then the old path is removed
on uninstall. Therefore the ``etc/`` directory created above has
vanished now::

  >>> ls('parts')
  d  foo
