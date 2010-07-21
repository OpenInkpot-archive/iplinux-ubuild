from contextlib import contextmanager
from tempfile import mkdtemp

__all__ = ['in_work_dir']

_TMPFS_SIZE='8g'

@contextmanager
def in_work_dir(priv, base):
    base.makedirs_p(0755)
    work_dir = mkdtemp(dir=base, prefix='builddir.')
    try:
        priv.check_run(['mount', '-t', 'tmpfs', '-o', 'size=' + _TMPFS_SIZE, 'tmpfs', work_dir])
        yield work_dir
    finally:
        if not priv.run(['umount', work_dir]):
            # FIXME: log
            pass
        work_dir.rmtree(True)
