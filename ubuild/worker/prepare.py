from ubuild.worker.pbuilder import int_exec

__all__ = ['prepare']

_SCRIPT = '''#!/bin/sh
cd '%s'
'%s/debian/source/prepare' "$@"
'''

def prepare(envdir, srcdir, args):
    if args:
        scriptfile = srcdir / 'preparesrc'
        with open(scriptfile, 'w') as fh:
            fh.write(_SCRIPT % (srcdir, srcdir))
        int_exec(envdir, srcdir, scriptfile, args)
