# -*- coding: utf-8 -*-
import os
import sys

from setuptools import setup, find_packages
from setuptools.command import install as origin

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

with open(os.path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

_install = origin.install


def _post_install(dir):
    from subprocess import call
    call(['python3', 'init.py'])  # executanto o script que criará os diretorios padrões sys.executable


class my_install(_install):
    def run(self):
        _install.run(self)
        self.execute(_post_install, (self.install_lib,),
                     msg="Running post install task")

setup(name='watchman',
      version='0.1',
      description='watchman',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Tornado",
          "Topic :: Internet :: WWW/HTTP"
      ],
      author='Anderson Marques Morais',
      author_email='andersonoanjo18@gmail.com',
      url='',
      keywords='monitoring web websocket ssh paramiko python3 tornado',
      packages=find_packages(exclude=['docs', 'scripts', 'dist', 'build', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      test_suite='',
      install_requires=requirements,
      cmdclass={'install': my_install}
      )
