from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from glob import glob
from os.path import basename, join
from os import getenv, chdir, unlink
from sys import platform

DEV = getenv('WITH_DEV')

chdir('src')

targets = [
    x for x in (
        (glob('*.py') + glob('*/*.py') if not DEV else []) +
        glob('*.pyx') + glob('*/*.pyx')
    )
    if not basename(x).startswith('_') and basename(x) != 'main.py'
]

setup(ext_modules=cythonize(targets))

if not DEV:
    for target in targets:
        unlink(target)


chdir('..')
