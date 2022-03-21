import cv2
import numpy as np

import pyk4a
from helpers import colorize
from pyk4a import Config, PyK4A, connected_device_count



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

    while 1:
        for i in range(cnt):
            capture = k4a[i].get_capture()
            if np.any(capture.color):
                cv2.imshow(f"k4a_color{i}", capture.color[:, :, :3])
                cv2.imshow(f"k4a_depth{i}", colorize(capture.depth, (None, 5000), cv2.COLORMAP_HSV))

                key = cv2.waitKey(10)
                if key != -1:
                    cv2.destroyAllWindows()
                    break
    k4a.stop()


if __name__ == "__main__":
    main()
