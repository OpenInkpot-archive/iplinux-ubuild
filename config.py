from ubuild.pbuilder_config import add_config

distros = {}

def iplinux(suite):
    return {
        'sign-key': 'F7E96648',
        'repos': [
            ('http://ftp.iplinux.org/iplinux/', suite, ['host/tools', 'host/cross']),
        ],
    }
distros['iplinux'] = iplinux

def openinkpot(suite):
    i = iplinux(suite)
    i['sign-key'] = '20DC1004'
    i['repos'].append(
        ('http://openinkpot.org/pub/oi/', suite, ['host/tools', 'host/cross'])
    )
    return i
distros['openinkpot'] = openinkpot

build_archs = {}
build_archs['i386'] = { 'build-arch': 'i386' }
build_archs['amd64'] = { 'build-arch': 'amd64' }

lenny = {
    'base-suite': 'lenny',
    'base-repo': 'http://localhost:9999/debian',
}

def add(distro, build_arch, branch):
    c = {}
    c.update(lenny)
    c.update(build_archs[build_arch])
    c.update(distros[distro](branch))
    add_config(distro + '-' + build_arch + '-' + branch, c)


for i in 'iplinux', 'openinkpot':
    for j in 'i386', 'amd64':
        for k in 'asimov', 'zelazny':
            add(i, j, k)
