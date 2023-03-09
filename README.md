sudo apt-get install redis-server

pip install redis


```python
from MsgManger.manager import NodeRegister

for i in range(1000):
    node = NodeRegister()
    node.pub("test", {"data": 1.23})
    node.wait_next_pub()