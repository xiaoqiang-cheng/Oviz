import redis
import json

defual_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)



class CreateObjectFromMsg(dict):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        if isinstance(value, (list, tuple)):
            if isinstance(value[0], (dict, list, tuple)):
                self[name] =  [CreateObjectFromMsg(x) for x in value]
            else:
                self[name] = value
        else:
            self[name] =  CreateObjectFromMsg(value) if isinstance(value, dict) else value
