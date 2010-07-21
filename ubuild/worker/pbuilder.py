import cPickle as pickle
from errno import ENOENT
from signal import SIGINT
from subprocess import call, check_call
from time import time

from path import path

from sig import signals_ignored
from workdir import in_work_dir

__all__ = ['prepare_env', 'build', 'int_exec']

_FORCE_UPDATE='''#!/bin/sh
/usr/bin/apt-get update
/usr/bin/apt-get dist-upgrade --yes --force-yes
'''
_UPDATE_TIMEOUT = 86400*7
_PBUILDER = '/usr/sbin/pbuilder'

def _safe_mtime(path):
    try:
        return path.stat().st_mtime
    except OSError, e:
        if e.errno == ENOENT:
            return 0
        raise

def _save_build_environment(envdir, env):
    with open(envdir / 'build-environment', 'w') as fh:
        pickle.dump(env, fh)

def _load_build_environment(envdir):
    with open(envdir / 'build-environment', 'r') as fh:
        return pickle.load(fh)

def _get_update_args(envdir):
    return

class SudoRunner(object):
    def run(self, args):
        with signals_ignored(SIGINT):
            return call(['sudo'] + args) == 0
    def check_run(self, args):
        with signals_ignored(SIGINT):
            check_call(['sudo'] + args)

def _get_common_args(envdir, builddir, env, tmp_basetgz=False, ext_bindmounts=[]):
    repo, other_repos = env.repositories[0], env.repositories[1:]
    opts = ['--configfile', envdir / 'pbuilderrc',
            '--hookdir', envdir / 'hooks',
            '--aptcache', envdir / 'cache',
            '--buildplace', builddir,
            '--debootstrap', 'debootstrap',
            '--mirror', repo.url,
            '--distribution', repo.suite,
            '--components', ' '.join(repo.components),
            '--debootstrapopts', '--arch=' + env.build_architecture]
    if tmp_basetgz:
        opts += ['--basetgz', envdir / 'base.tgz.tmp']
    else:
        opts += ['--basetgz', envdir / 'base.tgz' ]

    bindmounts = []
    str_repos = []
    for r in other_repos:
        if r.components:
            str_repos += [
                'deb %s %s %s' % (r.url, r.suite, ' '.join(r.components))
            ]
        else:
            str_repos += ['deb %s %s' % (r.url, r.suite)]
        if r.url.startswith('file:'):
            bindmounts += [r.url[5:]]
    bindmounts += ext_bindmounts
    if bindmounts:
        opts += ['--bindmounts', ' '.join(bindmounts)]
    if str_repos:
        opts += ['--othermirror', '|'.join(str_repos)]
    return opts

def _prepare_envdir(envdir):
    envdir.makedirs_p(0755)
    (envdir / 'pbuilderrc').write_bytes('APTCACHEHARDLINK=no')
    (envdir / 'hooks').mkdir_p(0755)
    (envdir / 'hooks' / 'D70update').write_bytes(_FORCE_UPDATE)
    (envdir / 'hooks' / 'D70update').chmod(0755)
    (envdir / 'cache').mkdir_p(0755)
    (envdir / 'version').write_bytes('1')

def _env_current_version(envdir):
    try:
        with open(envdir / 'version', 'r') as fh:
            version  = int(fh.read())
        if version == 1:
            return True
    except IOError, e:
        if e.errno == ENOENT:
            return False
    except ValueError:
        return False

def _update_needed(envdir):
    mtime = _safe_mtime(envdir / 'base.tgz')
    return mtime + _UPDATE_TIMEOUT < time()

def _create_basetgz(envdir, env, args):
    pbuilder_args = [_PBUILDER] + args
    with in_work_dir(SudoRunner(), envdir) as workdir:
        pbuilder_args += _get_common_args(envdir, workdir, env, True)
        SudoRunner().run(pbuilder_args)
    (envdir / 'base.tgz').unlink_p()
    (envdir / 'base.tgz.tmp').rename(envdir / 'base.tgz')

def prepare_env(envdir, env):
    if envdir.exists() and _env_current_version(envdir):
        if _update_needed(envdir):
            (envdir / 'base.tgz').link(envdir / 'base.tgz.tmp')
            _create_basetgz(envdir, env, ['--update', '--override-config'])
    else:
        if envdir.exists():
            envdir.rmtree(True)
        _prepare_envdir(envdir)
        _create_basetgz(envdir, env, ['--create'])
        _save_build_environment(envdir, env)

def build(envdir, srcpkg, workdir, outdir, build_options):
    env = _load_build_environment(envdir)
    buildopts = '-b'
    if build_options.target_arch:
        buildopts += ' -a'+ build_options.target_arch
    pbuilder_args = [_PBUILDER, '--build',
                     '--buildresult', outdir,
                     '--debbuildopts', buildopts,
                     '--logfile', outdir / 'build.log',
                     '--override-config']
    with in_work_dir(SudoRunner(), workdir) as builddir:
        pbuilder_args += _get_common_args(envdir, workdir, env)
        # FIXME: wrong?
        if build_options.arch_indep:
            pbuilder_args += ['--binary-arch']
        pbuilder_args += [srcpkg]

        print pbuilder_args
        SudoRunner().run(pbuilder_args)

    for f in outdir.listdir():
        if f.endswith('.changes'):
            return outdir / f

def int_exec(envdir, workdir, script, args=[]):
    env = _load_build_environment(envdir)
    with in_work_dir(SudoRunner(), workdir) as builddir:
        pbuilder_args = [_PBUILDER,
                         '--execute',
                         '--override-config'] + \
                         _get_common_args(envdir, builddir, env, False, [workdir]) + \
                        ['--',
                         script] + args
        SudoRunner().check_run(pbuilder_args)
