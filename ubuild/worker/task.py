#!/usr/bin/python

import json

from path import path

import cachegit
import prepare
import gensrc
import pbuilder
import sign
import crosser

from ubuild.build import Repository, Environment, Source, BuildOptions

def do_env(basedir, env):
    envdir = basedir / 'env' / env.name
    pbuilder.prepare_env(envdir, env)
    return envdir

def do_source(basedir, taskdir, source):
    srcdir = taskdir / 'src'
    cachedir = basedir / 'gitcache'
    cachegit.clone(cachedir, source.url, source.tag, srcdir)
    return srcdir

def do_prepare(envdir, srcdir, source):
    prepare.prepare(envdir, srcdir, source.prepare_arguments)

def do_srcpkg(envdir, srcdir, build_options):
    return gensrc.gensrc(envdir, srcdir, build_options.target_arch)

def do_build(envdir, srcpkg, taskdir, build_options):
    return pbuilder.build(envdir, srcpkg, taskdir, taskdir, build_options)

def do_cross(envdir, changesfile, cross_arch):
    if cross_arch:
        return crosser.cross(envdir, changesfile, cross_arch)
    else:
        return changesfile

def do_sign(changesfile):
    sign.sign(changesfile)

def run_task(basedir, task_id, env, source, build_options):
    taskdir = basedir / 'tasks' / str(task_id)

    if taskdir.exists():
        raise RuntimeError("Task directory %s already exists" % taskdir)

    taskdir.makedirs_p(0755)

    envdir = do_env(basedir, env)
    print envdir
    srcdir = do_source(basedir, taskdir, source)
    print srcdir
    do_prepare(envdir, srcdir, source)
    srcpkg = do_srcpkg(envdir, srcdir, build_options)
    print srcpkg
    result = do_build(envdir, srcpkg, taskdir, build_options)
    result = do_cross(envdir, result, build_options.cross_arch)
    do_sign(result)
    return result
