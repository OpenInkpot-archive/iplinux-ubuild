from contextlib import contextmanager
from sys import modules
from signal import signal

if not hasattr(modules['signal'], 'siginterrupt'):
    from ctypes import cdll
    libc = cdll.LoadLibrary('libc.so.6')
    if hasattr(libc, 'siginterrupt'):
        siginterrupt = libc.siginterrupt
else:
    from signal import siginterrupt

__all__ = ['signals_ignored']

@contextmanager
def signals_ignored(*signals):
    def _nop(signum, stackframe):
        pass

    oh = {}
    for s in signals:
        oh[s] = signal(s, _nop)
        siginterrupt(s, False)
    try:
        yield
    finally:
        for s in signals:
            signal(s, oh[s])
