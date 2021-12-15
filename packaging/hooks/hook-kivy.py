from os.path import join, basename
from kivy import kivy_modules_dir, kivy_data_dir
from kivy.utils import platform
from kivy.tools.packaging.pyinstaller_hooks import (
    add_dep_paths, get_factory_modules, kivy_modules)

add_dep_paths()

hiddenimports = []  # get_deps_all()['hiddenimports']
hiddenimports = list(set(
    get_factory_modules() + kivy_modules + hiddenimports))


hiddenimports += [
    'kivy.core',
    'kivy.core.clipboard',
    'kivy.core.clipboard._clipboard_ext',
    'kivy.core.clipboard._clipboard_sdl2',
    'kivy.core.clipboard.clipboard_dbusklipper',
    'kivy.core.clipboard.clipboard_gtk3',
    'kivy.core.clipboard.clipboard_sdl2',
    'kivy.core.clipboard.clipboard_winctypes',
    'kivy.core.clipboard.clipboard_xclip',
    'kivy.core.clipboard.clipboard_xsel',
    'kivy.core.gl',
    'kivy.core.image',
    'kivy.core.image.img_sdl2',
    'kivy.core.image._img_sdl2',
    'kivy.core.image.img_gif',
    'kivy.core.image.img_pil',
    'kivy.core.text',
    'kivy.core.text.text_sdl2',
    'kivy.core.text._text_sdl2',
    'kivy.core.text.markup',
    'kivy.core.text.text_layout',
    'kivy.core.text.text_sdl2',
    'kivy.core.window',
    'kivy.core.window._window_sdl2',
    'kivy.core.window.window_sdl2',
    'kivy.core.window.window_info',
    'kivy.graphics',
    'kivy.graphics.buffer',
    'kivy.graphics.cgl',
    'kivy.graphics.cgl_backend',
    'kivy.graphics.cgl_backend.cgl_debug',
    'kivy.graphics.cgl_backend.cgl_gl',
    'kivy.graphics.cgl_backend.cgl_glew',
    'kivy.graphics.cgl_backend.cgl_mock',
    'kivy.graphics.cgl_backend.cgl_sdl2',
    'kivy.graphics.compiler',
    'kivy.graphics.context',
    'kivy.graphics.context_instructions',
    'kivy.graphics.fbo',
    'kivy.graphics.gl_instructions',
    'kivy.graphics.instructions',
    'kivy.graphics.opengl',
    'kivy.graphics.opengl_utils',
    'kivy.graphics.scissor_instructions',
    'kivy.graphics.shader',
    'kivy.graphics.stencil_instructions',
    'kivy.graphics.texture',
    'kivy.graphics.transformation',
    'kivy.graphics.vbo',
    'kivy.graphics.vertex',
    'kivy.graphics.vertex_instructions',
]

hiddenimports.extend(
    [
        'Cryptodome',
        'Cryptodome.Hash.SHA',
        'Cryptodome.Hash.SHA256',
        'Cryptodome.PublicKey',
        'Cryptodome.PublicKey.RSA',
        'Cryptodome.Signature',
        'Cryptodome.Signature.PKCS1_v1_5',
        'Queue',
        'kivy.network.urlrequest',
        'numpy.core.multiarray',
        'ssl',
        'utils',
        'utils.math',
        'win32com',
        'win32gui',
        'win32timezone',
        'wmi',
        'screeninfo',
        'oscpy',
    ]
)

datas = [
    (kivy_data_dir, join('kivy_install', basename(kivy_data_dir))),
    (kivy_modules_dir, join('kivy_install', basename(kivy_modules_dir)))
]

print("used patched hooks")
