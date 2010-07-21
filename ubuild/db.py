import redis

db = redis.Redis()

def dbget(objtype, objid, objprop):
    return db.get('%s:%s:%s' % (objtype, objid, objprop))

def dblrange(objtype, objid, objprop, start, end):
    return db.lrange('%s:%s:%s' % (objtype, objid, objprop), start, end)

def dbsismember(objtype, objid, objprop, member):
    return db.sismember('%s:%s:%s' % (objtype, objid, objprop), member)

def dbsmembers(objtype, objid, objprop):
    return db.smembers('%s:%s:%s' % (objtype, objid, objprop))
