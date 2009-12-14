from distutils.core import setup

setup(name='ubuild',
      version='0.1',
      packages=['ubuild'],
      scripts=['scripts/ubuild'],
      data_files=[('/etc/ubuild', ['config.py'])])
