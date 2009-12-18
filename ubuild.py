#!/usr/bin/python

import sys
sys.path[:0] = ['/etc/ubuild']

import config
from ubuild.pbuilder import build
from optparse import OptionParser as optparser

_usage='''%name [-B] <configuration> <.dsc> <mode> <output-dir>

 <mode> = host | target:$arch

 Configuration is like openinkpot-i386-asimov or iplinux-amd64-zelazny'''


def main():
    parser = optparser(usage=_usage)
    parser.add_option('-B', action='store_true', dest='arch_dep_only', default=False)

    (opts, args) = parser.parse_args()

    if len(args) != 4:
        parser.print_help()
        return 1

    (configuration, dscfile, mode, output_dir) = args

    if mode == 'host' or mode.startswith('target:'):
        if mode == 'host':
            arch = None
        else:
            arch = mode[7:]
        if build(dscfile, configuration, opts.arch_dep_only, output_dir, arch):
            return 0
        else:
            return 1

    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())
