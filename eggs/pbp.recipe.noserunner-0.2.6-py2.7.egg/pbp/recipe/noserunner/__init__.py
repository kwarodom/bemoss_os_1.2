# -*- coding: utf-8 -*-
import os, sys
import pkg_resources
import zc.buildout.easy_install
import zc.recipe.egg

class Recipe(object):

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options
        options['script'] = os.path.join(buildout['buildout']['bin-directory'],
                                         options.get('script', self.name),
                                         )
        wd = options.get('working-directory', '').strip()
        if wd == '':
            options['location'] = os.path.join(
                buildout['buildout']['parts-directory'], name)
        eggs = options.get('eggs', '')
        eggs = [egg.strip() for egg in eggs.split('\n') if egg.strip() != '']
        if 'nose' not in eggs:
            eggs.append('nose')
        options['eggs'] = '\n'.join(eggs)
        self.egg = zc.recipe.egg.Egg(buildout, name, options)

    def install(self):
        options = self.options
        dest = []
        eggs, ws = self.egg.working_set(('nose', ))

        test_paths = [ws.find(pkg_resources.Requirement.parse(spec)).location
                      for spec in eggs]

        defaults = options.get('defaults', '').strip()
        if defaults:
            defaults = ['nose'] + defaults.split()
            defaults = "argv=%s+sys.argv[1:]" % defaults
        else:
            defaults = "argv=['nose']+sys.argv[1:]"

        wd = options.get('working-directory', '').strip()
        if wd != '':
            if os.path.exists(wd):
                assert os.path.isdir(wd)
            else:
                os.mkdir(wd)
            dest.append(wd)
            initialization = initialization_template % wd
        else:
            initialization = ''

        env_section = options.get('environment', '').strip()
        if env_section:
            env = self.buildout[env_section]
            for key, value in env.items():
                initialization += env_template % (key, value)
            initialization = 'import os\n%s' % initialization

        initialization_section = options.get('initialization', '').strip()
        if initialization_section:
            initialization += initialization_section

        dest.extend(zc.buildout.easy_install.scripts(
            [(options['script'], 'nose', 'main')],
            ws, options['executable'],
            self.buildout['buildout']['bin-directory'],
            extra_paths=self.egg.extra_paths,
            arguments = defaults,
            initialization = initialization,
            ))

        return (os.path.join(self.buildout['buildout']['bin-directory'],
                options['script']),)

    update = install

arg_template = """[
  '--test-path', %(TESTPATH)s,
  ]"""

initialization_template = """\
import os

sys.argv[0] = os.path.abspath(sys.argv[0])
os.chdir(%r)
"""

env_template = """os.environ['%s'] = %r
"""

