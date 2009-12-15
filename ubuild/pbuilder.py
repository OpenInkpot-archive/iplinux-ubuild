#
# low-level pbuilder controller
#

from __future__ import with_statement

if True:
    from sys import modules
    import signal
    if not hasattr(modules['signal'], 'siginterrupt'):
        from ctypes import cdll
        libc = cdll.LoadLibrary('libc.so.6')
        if hasattr(libc, 'siginterrupt'):
            signal.siginterrupt = libc.siginterrupt

from contextlib import contextmanager
from errno import ENOENT, EEXIST
from os import unlink, R_OK, getenv, makedirs, environ
from path import path
from pbuilder_config import _configs
from signal import SIGINT, signal, siginterrupt
from stat import S_IXUSR
from subprocess import call, check_call
from tempfile import mkdtemp
from time import time

__all__ = ['build', 'put_packages_into_repo']

# FIXME
_base_dir = path(getenv('HOME')) / '__build'
_update_timeout = 86400*7
_tmpfs_size = '2G'
_parallel_builds = 8
_pbuilder = 'pbuilder'
# ENDFIXME

def safe_unlink(path):
    try:
        unlink(path)
    except OSError, e:
        if e.errno != ENOENT:
            raise

def safe_mtime(path):
    try:
        s = path.stat()
        return s.st_mtime
    except OSError, e:
        if e.errno == ENOENT:
            return 0
        raise

def safe_makedirs(path, mode=0777):
    try:
        makedirs(path, mode)
    except OSError, e:
        if e.errno != EEXIST:
            raise
path.safe_makedirs = safe_makedirs

@contextmanager
def signals_ignored(*signals):
    def _nop(signum, stackframe):
        pass

    oh = {}
    for s in signals:
        oh[s] = signal(s, _nop)
        siginterrupt(s, False)
    try:
        yield
    finally:
        for s in signals:
            signal(s, oh[s])

class SudoRunner(object):
    def run(self, args):
        with signals_ignored(SIGINT):
            return call(['sudo'] + args) == 0
    def check_run(self, args):
        with signals_ignored(SIGINT):
            check_call(['sudo'] + args)

@contextmanager
def in_work_dir(priv):
    _base_dir.safe_makedirs(0755)
    work_dir = mkdtemp(dir=_base_dir, prefix='builddir.')
    try:
        priv.check_run(['mount', '-t', 'tmpfs', '-o', 'size=' + _tmpfs_size, 'tmpfs', work_dir])
        yield work_dir
    finally:
        if not priv.run(['umount', work_dir]):
            # FIXME: log
            pass
        work_dir.rmtree(True)

def _get_common_opts(config_name, work_dir):
    # Sigh. This is not overridable using command-line options
    rc_file = _base_dir / 'pbuilderrc'
    if not rc_file.exists():
        rc_file.write_text('APTCACHEHARDLINK=no\n')
        rc_file.write_text('DEB_BUILD_OPTIONS=parallel=%s\n' % _parallel_builds,
                           append=True)
    # Sigh again.
    hooks_dir = _base_dir / 'hooks'
    if not hooks_dir.exists():
        hooks_dir.safe_makedirs(0755)
        apt_update_hook = hooks_dir / 'D70update'
        apt_update_hook.write_text('''#!/bin/sh
/usr/bin/apt-get update
/usr/bin/apt-get dist-upgrade --yes --force-yes
''')
        apt_update_hook.chmod(apt_update_hook.stat().st_mode | S_IXUSR)

    cache_dir = _base_dir / 'cache'
    repo_dir = _base_dir / 'repo'

    cache_dir.safe_makedirs(0755)
    repo_dir.safe_makedirs(0755)

    repo_pkg_file = repo_dir / 'Packages'
    if not repo_pkg_file.exists():
        repo_pkg_file.write_text('')

    opts = ['--configfile', rc_file,
            '--hookdir', hooks_dir,
            '--aptcache', cache_dir,
            '--buildplace', work_dir,
            '--debootstrap', 'debootstrap',
            '--basetgz', _basearchive_name(config_name),
            '--mirror', _configs[config_name]['base-repo'],
            '--distribution', _configs[config_name]['base-suite'],
            '--debootstrapopts', '--arch=' + _configs[config_name]['build-arch'],
            '--bindmounts', repo_dir]

    str_repos = []
    for repo in _configs[config_name]['repos'] + [('file://' + repo_dir, './', [])]:
        if len(repo[2]) > 0:
            str_repos += ['deb %s %s %s' % (repo[0], repo[1], ' '.join(repo[2]))]
        else:
            str_repos += ['deb %s %s' % (repo[0], repo[1])]
    if str_repos:
        opts += ['--othermirror', '|'.join(str_repos)]

    if 'DEBUG' in environ:
	opts += ['--debug']

    return opts

def _get_update_args(config_name, work_dir):
    return [_pbuilder, '--update', '--override-config'] + \
        _get_common_opts(config_name, work_dir)

def _get_create_args(config_name, work_dir):
    return [_pbuilder, '--create'] + \
        _get_common_opts(config_name, work_dir)

def _get_build_args(dsc_file, arch_dep_only, target_arch, log_file, config_name, out_dir, work_dir):
    debbuildopts = '-b'

    args = [_pbuilder, '--build',
            '--buildresult', out_dir,
            '--debbuildopts', debbuildopts,
            '--logfile', log_file,
            '--override-config'] + \
            _get_common_opts(config_name, work_dir)
    if target_arch:
        args += ['--target-arch', target_arch]
    if arch_dep_only:
        args += ['--binary-arch']
    return args + [dsc_file]

def _basearchive_name(config_name):
    return _base_dir / config_name + '.tgz'

def _basearchive_needs_updating(config_name):
    mtime = safe_mtime(_basearchive_name(config_name))
    return mtime + _update_timeout < time()

def _run(priv, options):
    return priv.run(options)

def _gen_basearchive(priv, config_name, pb_options):
    basearchive = _basearchive_name(config_name)
    if not _run(priv, pb_options):
        safe_unlink(basearchive)
        return False
    return True

def _prepare_basearchive(config_name, priv, work_dir):
    basearchive = _basearchive_name(config_name)
    if basearchive.exists():
        if _basearchive_needs_updating(config_name):
            pb = _get_update_args(config_name, work_dir)
            return _gen_basearchive(priv, config_name, pb)
        else:
            return True
    else:
        pb = _get_create_args(config_name, work_dir)
        return _gen_basearchive(priv, config_name, pb)

def _build(dscfilename, config_name, arch_dep_only, target_arch, priv, out_dir, work_dir):
    # foo.dsc -> foo_i386.log
    log = dscfilename[:-4] + '_' + _configs[config_name]['build-arch'] + '.log'
    pb = _get_build_args(dscfilename, arch_dep_only, target_arch, log, config_name, out_dir, work_dir)
    return _run(priv, pb)

#
# In <- .dsc, configuration, various options
# Out -> .changes
#
def build(dscfilename,
          config_name,
          arch_dep_only,
          out_dir,
          target_arch=None,
          priv=SudoRunner()):
    with in_work_dir(priv) as work_dir:
        if not _prepare_basearchive(config_name, priv, work_dir):
            return
        return _build(dscfilename, config_name, arch_dep_only, target_arch, priv, out_dir, work_dir)

def get_repo_dir(config_name):
    return _base_dir / 'repo'

def _put_package_into_repo(config_name, package):
    if not package.endswith('.deb'):
        raise ValueError('Wrong filename supplied: %s' % package)
    path(package).copy(get_repo_dir(config_name))

def _regenerate_repo(config_name):
    raise NotImplementedError()

def put_packages_into_repo(config_name, packages):
    for package in packages:
        _put_package_into_repo(config_name, package)
    _regenerate_repo(config_name)
