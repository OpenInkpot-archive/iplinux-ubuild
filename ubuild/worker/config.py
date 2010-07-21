from ConfigParser import RawConfigParser
from path import path

_CONFIG = "~/.ubuildrc"

__all__ = ['get']

def get(section, option):
    return _config.get(section, option)

def read_config(filename):
    cp = RawConfigParser()
    cp.read([filename])
    return cp

_config = read_config(path(_CONFIG).expanduser())

