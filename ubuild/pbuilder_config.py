
_configs = {}

_required_keys = set([
    'sign-key',
    'repos',
    'build-arch',
    'base-suite',
    'base-repo',
])

def add_config(name, config):
    config_keys = set(config.keys())
    if name in _configs:
        raise KeyError('Config %s is already registered' % name)
    if config_keys != _required_keys:
        missing = _required_keys - config_keys
        extra = config_keys - _required_keys
        raise ValueError('Wrong configuration supplied. ' +
                         'Missing items: %s. Extra items: %s' %
                         (', '.join(missing), ', '.join(extra)))
    _configs[name] = config
