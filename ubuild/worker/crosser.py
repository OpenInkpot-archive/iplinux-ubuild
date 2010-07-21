'''
This piece of code traverses .changes file and amends it with new .deb packages
created by dpkg-cross.
'''

from re import compile

from debian.deb822 import Changes
from debian.debfile import DebFile

from ubuild.worker.pbuilder import int_exec

__all__ = ['cross']

RE = compile('^Building (\S+\.deb)$')


#
# _needs_crossing and _cross_only are _policy_, not _mechanism_. It might be
# useful to move this info out of worker and push the "what to cross"
# information from main node, but current code will serve us just fine for a
# while, as long as all sections that need not to be crossed are started with
# 'host/'.
#
def _needs_crossing(fileinfo):
    return not fileinfo['section'].startswith('host/')

def _cross_only(fileinfo):
    return fileinfo['section'] == 'libdevel'

_SCRIPT = '''#!/bin/sh -x
apt-get install --yes --force-yes dpkg-cross
cd '%s'
dpkg-cross -A -a '%s' -b '%s' > %s
'''

def _cross_deb(envdir, changesfile, fileinfo, target_arch):
    scriptfile = changesfile.parent / (fileinfo['name'] + 'cross-script')
    logfile = fileinfo['name'] + '.dpkg-cross.log'
    with open(scriptfile, 'w') as fh:
        fh.write(_SCRIPT % (changesfile.parent, target_arch, fileinfo['name'], logfile))

    int_exec(envdir, changesfile.parent, scriptfile)

    with open(changesfile.parent / logfile, 'r') as fh:
        for line in fh:
            m = RE.match(line)
            if m:
                return changesfile.dirname() / m.group(1)

def _add_deb(changes, filename):
    d = DebFile(filename)

    changes['Files'].append({
        'name': filename.basename(),
        'size': filename.getsize(),
        'md5sum': filename.read_hash('md5').encode('hex'),
        'section': d.debcontrol()['Section'],
        'priority': d.debcontrol()['Priority'],
    })
    changes['Checksums-Sha1'].append({
        'name': filename.basename(),
        'size': filename.getsize(),
        'sha1': filename.read_hash('sha1').encode('hex')
    })
    changes['Checksums-Sha256'].append({
        'name': filename.basename(),
        'size': filename.getsize(),
        'sha256': filename.read_hash('sha256').encode('hex')
    })

def _remove_checksum(checksums, filename):
    for cs in checksums:
        if cs['Name'] == filename:
            checksums.remove(cs)
            return

def _remove_deb(changes, fileinfo):
    changes['Files'].remove(fileinfo)
    _remove_checksum(changes['Checksums-Sha1'], fileinfo['Name'])
    _remove_checksum(changes['Checksums-Sha256'], fileinfo['Name'])

def cross(envdir, changesfile, target_arch):
    with open(changesfile, 'r') as fh:
        changes = Changes(fh)

    new_debs = []
    removed_debs = []
    for fi in changes['Files']:
        print fi
        if _needs_crossing(fi):
            cross_deb_name = _cross_deb(envdir, changesfile, fi, target_arch)
            new_debs.append(cross_deb_name)
            if _cross_only(fi):
                removed_debs.append(fi)
    for cross_deb_name in new_debs:
        _add_deb(changes, cross_deb_name)
    for fileinfo in removed_debs:
        _remove_deb(changes, fileinfo)

    out = changesfile.stripext() + '.cross.changes'
    with open(out, 'w') as ofh:
        changes.dump(ofh)
    return out
