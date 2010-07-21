'''
This module generates Debian source package (.dsc + .tar.gz) from given
directory with unpacked tree.

Additionally it processes XCS-Cross* headers in debian/control and rewrites them
into standard Build-Depends field, so the resulting .dsc may be processed by
unpatched pbuilder.
'''

from re import compile
from debian.deb822 import Deb822

from ubuild.worker.pbuilder import int_exec

__all__ = ['gensrc']

RE = compile('^dpkg-source: info: building \S+ in (\S+\.dsc)$')

CROSS_RE = compile('(\s*)([a-z0-9+.-]+)(.*)')

def _cross_dep(deps, arch):
    for dep in deps.split(','):
        m = CROSS_RE.match(dep)
        yield ('%s%s-%s-cross%s' % (m.group(1), m.group(2), arch, m.group(3))).strip()

def _expand_build_depends(src, dest, arch):
    with open(src, 'r') as fd:
        control = Deb822(fd)
    deps = []
    if 'XCS-Needs-Cross-Toolchain' not in control or \
            control['XCS-Needs-Cross-Toolchain'] != 'no':
        deps += [arch + '-cross-toolchain']
    if 'XCS-Cross-Host-Build-Depends' in control:
        deps += control['XCS-Cross-Host-Build-Depends'].split(',')
    if 'XCS-Cross-Build-Depends' in control:
        deps += _cross_dep(control['XCS-Cross-Build-Depends'], arch)
    control['Build-Depends'] = ', '.join(deps)
    with open(dest, 'w') as ofd:
        control.dump(ofd)

_SCRIPT = '''#!/bin/sh
cd '%s'
dpkg-source -I.git %s -b '%s' > dpkg-source.log
'''

def gensrc(envdir, srcdir, target_arch=None):
    '''
    envdir - directory of pbuilder environment
    srcdir - directory of unpacked source code
    '''
    # We need to pass -I.git as there are 1.0 packages

    scriptfile = srcdir.parent / 'gensrc'

    if target_arch:
        _expand_build_depends(srcdir / 'debian' / 'control',
                              srcdir.parent / 'control.native',
                              target_arch)
        controlarg = '-c' + srcdir.parent / 'control.native'
    else:
        controlarg = ''

    with open(scriptfile, 'w') as fh:
        fh.write(_SCRIPT % (srcdir.parent, controlarg, srcdir.name))

    int_exec(envdir, srcdir.parent, scriptfile)

    with open(srcdir.parent / 'dpkg-source.log', 'r') as fh:
        for line in fh:
            m = RE.match(line)
            if m:
                return srcdir.parent / m.group(1)
