import os
import time

    
path = './record/20220329_021439_0_0.mkv'    
    
for i in range(50):
    print(os.path.getsize(path))
    time.sleep(0.5)
    
