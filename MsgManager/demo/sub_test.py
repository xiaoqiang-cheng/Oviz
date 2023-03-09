import sys
sys.path.append("..")

# -----------sub demo code -------------
from manager import NodeRegister
import time

node = NodeRegister()

def msg1_call(msg, topic):
    print("timestamp1:", time.time())
    # print(msg.author)
    # print(msg.version)
    print(msg)

def msg2_call(msg, topic):
    print("timestamp2:", time.time())
    # print(msg.author)
    # print(msg.version)
    print(msg)

node.sub("test1", msg1_call)
node.sub("test2", msg2_call)

node.subspin()
print("====")