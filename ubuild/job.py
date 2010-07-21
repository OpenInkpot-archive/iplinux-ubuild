from ubuild.db import db

class Job(object):
    def __init__(self, id=None, name=None):
        if not id:
            self.id = db.incr('jobs:max-id')
            self._set('name', name)
            self._set('status', 'running')
            db.sadd('jobs', self.id)
        else:
            self.id = id

    def name(self):
        return self._get('name')

    def status(self):
        return self._get('status')

    def _set(self, key, value):
        db.set('job:%s:%s' % (self.id, key), value)

    def _get(self, key):
        return db.get('job:%s:%s' % (self.id, key))
