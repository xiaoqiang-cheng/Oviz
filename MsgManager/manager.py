from .utils import *
from types import FunctionType, MethodType
import json
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
                              np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class NodeRegister(object):
    def __init__(self) -> None:
        super().__init__()
        self.node = redis.StrictRedis(connection_pool=defual_pool)
        self.suber = self.node.pubsub()
        self.subcall = {}
        self.suber.subscribe("control")
        self._step = 0


    def pub(self, topic : str, msg):
        if isinstance(msg, dict):
            # self.node.publish(topic, str(msg))
            data = json.dumps(msg, cls=NumpyEncoder)
            self.node.publish(topic, data)
        elif isinstance(msg, object):
            # self.node.publish(topic, str(msg.__dict__))
            data = json.dumps(msg, default=lambda o:o.__dict__)
            self.node.publish(topic, data)
        else:
            print("不支持的消息类型")

    def sub(self, topic : str, callback: FunctionType):
        if isinstance(callback, (FunctionType,MethodType)):
            self.suber.subscribe(topic)
            self.subcall[topic] = callback
        else:
            print("需要指定回调函数")

    def wait_next_pub(self, wait = True):
        if wait == True:
            for item in self.suber.listen():
                if item['type']=='message':
                    data = item['data'].decode()
                    data = eval(data)
                    topic = item['channel'].decode()
                    if topic == "control":
                        self._step == data["data"]
                        break


    def subspin(self):
        for item in self.suber.listen():
            if item['type']=='message':
                data = item['data'].decode()
                data = eval(data)
                topic = item['channel'].decode()
                # msg = CreateObjectFromMsg(data)
                if topic == "control":
                    continue
                self.subcall[topic](data, topic)

    def unsub(self, topic : str):
        try:
            self.suber.unsubscribe(topic)
            self.subcall.pop(topic)
        except:
            print("没有找到当前话题:%s" %topic)





