import cv2
import numpy as np

import pyk4a
from helpers import colorize
from pyk4a import Config, PyK4A, connected_device_count

import threading

def main():
    cnt = connected_device_count()
    if not cnt:
        print("No devices available")
        exit()
    k4a = []
    for i in range(cnt):
        print(i)
        k4a.append(PyK4A(
            config=Config(
                color_resolution=pyk4a.ColorResolution.RES_720P,
                depth_mode=pyk4a.DepthMode.NFOV_UNBINNED,
                synchronized_images_only=True,
            ),
            device_id=i
        ))
        k4a[i].start()

        # getters and setters directly get and set on device
        k4a[i].whitebalance = 4500
        assert k4a[i].whitebalance == 4500
        k4a[i].whitebalance = 4510
        assert k4a[i].whitebalance == 4510

    def viewer(k4a,num):
        while 1:
            capture = k4a.get_capture()
            if np.any(capture.color):
                cv2.imshow(f"k4a_color{num}", capture.color[:, :, :3])
                cv2.imshow(f"k4a_depth{num}", colorize(capture.depth, (None, 5000), cv2.COLORMAP_HSV))

                key = cv2.waitKey(10)
                if key != -1:
                    cv2.destroyAllWindows()
                    k4a.stop()
                    break
    th_list = []
    for i in range(cnt):
        tmp = threading.Thread(target=lambda : viewer(k4a[i],i))
        tmp.start()
        th_list.append(tmp)
if __name__ == "__main__":
    main()
