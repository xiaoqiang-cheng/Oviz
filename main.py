from Oviz import Oviz
import numpy as np

for i in range(10):
    fake_img = np.ones((720, 720, 3), dtype=np.uint8) * i * 10
    Oviz.imshow(fake_img)
    print(i)
    Oviz.waitKey()


