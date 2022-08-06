import os
NAME = os.getenv("NAME")
DEBUG = os.getenv("DEBUG")
from os.path import join
import kivy
from kivy.utils import platform

if platform == 'win':
    from kivy_deps import sdl2, glew
else:
    glew = sdl2 = None


IS_LINUX = os.name == 'posix' and os.uname()[0] == 'Linux'
if IS_LINUX:
    from PyInstaller.depend import dylib
    dylib._unix_excludes.update({
        r'.*nvidia.*': 1,
        r'.*libdrm.*': 1,
	r'.*hashlib.*': 1,
        })

    dylib.exclude_list = dylib.ExcludeList()

binexcludes = [
     'gobject', 'gio', 'gtk', 'gi', 'wx', 'twisted', 'curses',
     'gstreamer', 'libffi', 'libglib', 'libmikmod', 'libflac', 'libvorbis',
     'libgstreamer', 'libvorbisfile', 'include', 'libstdc++.so.6',
     'gst_plugins', 'liblapack', 'pygame', 'lib/', 'include', 'kivy_install/modules',
]

hookspath = os.path.join(os.path.abspath(os.path.dirname('.')), 'packaging', 'hooks')

a = Analysis(
    ['../src/main.py'],
    pathex=['src'],
    hookspath=[hookspath],
    runtime_hooks=[
        os.path.sep.join(
            (
            os.path.dirname(kivy.__file__), 'tools', 'packaging',
            'pyinstaller_hooks', 'pyi_rth_kivy.py'
            )
        ),
        os.path.sep.join((hookspath, 'fix_factory.py'))
    ],
    excludes=binexcludes
)

pyz = PYZ(a.pure)

name = '%s%s' % (NAME, '.exe' if os.name == 'nt' else '')

def not_in(x, binexcludes):
    return not any(y in x.lower() for y in binexcludes)

a.binaries = [
    x for x in a.binaries
    if not_in(x[0], binexcludes)
]

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=name,
          debug=DEBUG,
          strip=None,
          upx=True,
          console=DEBUG,
          icon=join('src', 'data', 'icons', 'icon.ico'))

with open('packaging/blacklist.txt') as f:
    excludes = [x.strip() for x in f.readlines()]

coll = COLLECT(exe,
               Tree('src', excludes=excludes),
               a.binaries,
               a.zipfiles,
               a.datas,
               *([Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)] if sdl2 else []),
               strip=None,
               upx=True,
               name=NAME+DEBUG)

app = BUNDLE(coll,
             name='{}.app'.format(NAME),
             icon='icon.icns',
             bundle_identifier='com.tangibledisplay.{}'.format(NAME),
         info_plist={
             'CFBundleExecutable': 'MacOs/{}.sh'.format(NAME)
         })
