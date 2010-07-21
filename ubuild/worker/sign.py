import config
from subprocess import check_call

__all__ = ['sign']

def sign(changesfile):
    check_call(['debsign', '--noconf', '-k' + config.get('sign', 'keyid'),
                '-pgpg', changesfile])


