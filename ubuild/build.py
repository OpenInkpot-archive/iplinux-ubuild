from ubuild.db import dbget, dblrange, dbsismember, dbsmembers

class Repository(object):
    def __init__(self, url, suite, components=None):
        self.url = url
        self.suite = suite
        self.components = components

def get_repository(name):
    return Repository(dbget('repo', name, 'url'),
                      dbget('repo', name, 'suite'),
                      dblrange('repo', name, 'components', 0, -1))

class Environment(object):
    def __init__(self, name, repositories, build_architecture):
        self.name = name
        self.repositories = repositories
        self.build_architecture = build_architecture

def get_environment(env_name, build_architecture):
    name = dbget('env', env_name, 'name')
    repositories = [get_repository(name) for name in dblrange('env', env_name, 'repositories', 0, -1)]
    if not dbsismember('env', env_name, 'build-architectures', build_architecture):
        raise RuntimeError(build_architecture, 'is not amongst allowed build architectures for %s: %s' % (env_name, ', '.join(dbsmembers('env', env_name, 'build-architectures'))))
    return Environment(name, repositories, build_architecture)

def get_git(env_name, pkgname):
    return dbget('env', env_name, 'gitbase') % pkgname

def get_tag(pkgversion):
    return pkgversion.replace(':', '+').replace('~', '.')

class Source(object):
    def __init__(self, url, tag, prepare_arguments=[]):
        self.url = url
        self.tag = tag
        self.prepare_arguments = prepare_arguments

def get_source(env_name, package_name, package_version, prepare_arguments=[]):
    return Source(get_git(env_name, package_name),
                  get_tag(package_version), prepare_arguments)

class BuildOptions(object):
    def __init__(self, arch_indep, target_arch, cross_arch):
        self.arch_indep = arch_indep
        self.target_arch = target_arch
        self.cross_arch = cross_arch
