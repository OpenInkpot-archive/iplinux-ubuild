'''
This module provides cache for 'git clone' / 'git fetch' operations.
'''

from git import Repo, Tag
from path import path

__all__ = ['clone', 'UnableToFetch']

class UnableToFetchError(Exception):
    pass

def _has_head(repo, head_name):
    for head in repo.heads:
        if head_name == head.name:
            return True

#
# FIXME: is it necessary to lock cache repositories? It makes sense unless git
# is able to cope with simultaneous r/w access.
#
# todir is guarenteed to be unique by caller, so only potentially shared
# resource is cache.
#

def clone(cachedir, url, tag, todir):
    '''
    Fetches tag <tag> from git repository by URL <url> into directory <todir>
    (creating git repository there if needed).

    Uses <cachedir> as a directory to store cache.
    '''
    cachedir = cachedir / url.replace(':', '-').replace('/', '-').replace('.', '-')
    ref = 'refs/tags/%s' % tag

    todir.makedirs_p(0755)
    if cachedir.exists() and cachedir.isdir():
        cr = Repo(cachedir)
        r = cr.clone(todir, origin='cache', quiet=True)
    else:
        r = Repo.init(todir)

    origin = r.create_remote('origin', url)
    try:
        origin.fetch('+%s:%s' % (ref,ref), quiet=True)
    except AssertionError:
        raise UnableToFetchError(url, ref)

    if _has_head(r, 'build'):
        r.heads.build.ref = Tag(r, ref).commit
    else:
        r.create_head('build', Tag(r, ref).commit)
    r.heads.build.checkout(force=True)

    if cachedir.exists() and cachedir.isdir():
        r.remote('cache').push(ref, force=True)
    else:
        cachedir.makedirs_p(0755)
        cr = r.clone(cachedir, bare=True, quiet=True)
