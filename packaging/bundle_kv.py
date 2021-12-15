from tempfile import mkstemp
from os.path import join
from os import walk, unlink, close, write
from shutil import move


def get_kv_source(fn):
    kv = fn[:-2] + 'kv'
    with open(kv, encoding='utf8') as f:
        source = f.read()
        res = source.replace('\\', r'\\')
    unlink(kv)
    return res


for root, dirnames, filenames in walk('src'):
    for f in filenames:
        fn = join(root, f)
        if f.endswith('.py'):
            tmp, tmpname = mkstemp()
            with open(fn, encoding='utf8') as source:
                found = False
                for line in source:
                    if line.endswith('load_kv()\n'):
                        found = True
                        line = line.replace('load_kv()', '{}')
                        write(tmp, b'from kivy.lang.builder import Builder\n')
                        write(tmp, line.format('Builder.load_string("""').encode('utf8'))
                        write(tmp, get_kv_source(fn).encode('utf8'))
                        write(tmp, b'""")')
                    else:
                        write(tmp, line.encode('utf8'))
            close(tmp)
            if found:
                unlink(fn)
                move(tmpname, fn)
                print(f"replaced {fn}")
            else:
                unlink(tmpname)
                print(f"skipped {fn}")
