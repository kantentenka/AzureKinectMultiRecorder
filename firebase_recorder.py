import cv2
import numpy as np

import pyk4a
from helpers import colorize
from pyk4a import Config, PyK4A, connected_device_count, PyK4ARecord

import threading

import datetime



file_name = "test"
def cnt_device():
    cnt = connected_device_count()
    
    print(f"{cnt} device(s) connected")
    return cnt

is_recording = False

class Recorder():
    def __init__(self):
        tdatetime = datetime.datetime.now()
        tstr = tdatetime.strftime('%Y%m%d_%H%M%S')
        self.file_name = tstr
        self.is_recording = False
        self.cnt = cnt_device()
        self.k4a = []
        self.record = []
        self.config=Config(            
            color_resolution=pyk4a.ColorResolution.RES_720P,
            depth_mode=pyk4a.DepthMode.NFOV_UNBINNED,
            synchronized_images_only=True,
        )
    def init_device(self):
        self.is_recording = True
        for i in range(self.cnt):
            print(i)
            
            self.k4a.append(PyK4A(
                config = self.config,
                device_id=i
            ))
            self.k4a[i].start()

            # getters and setters directly get and set on device
            self.k4a[i].whitebalance = 4500
            assert self.k4a[i].whitebalance == 4500
            self.k4a[i].whitebalance = 4510
            assert self.k4a[i].whitebalance == 4510
    def is_k4a(self):
        return len(self.k4a)>0
    def start(self,file_name):
        self.file_name = file_name
        self.is_recording = True
        if not self.cnt:
            print("No devices available")
            exit()
        
        if not(self.is_k4a()):
            print("device init")
            self.init_device()
        self.record = []
        print(len(self.k4a)>0)
        for i in range(self.cnt):
            self.record.append(PyK4ARecord(
                device=self.k4a[i],
                config=self.config,
                path=f"./record/{file_name}_{i}.mkv")
                          )
            self.record[i].create()

        th_list = []
        for i in range(self.cnt):
            tmp = threading.Thread(target=lambda : self.recorder(self.k4a[i],self.record[i],i))#,daemon=True)
            tmp.start()
            th_list.append(tmp)


    def recorder(self,k4a,record,num):
        cnt = 0
        while self.is_recording:
            
            capture = k4a.get_capture()
            record.write_capture(capture)
            if cnt != record.captures_count:
                print(f"device {num} captured,frame {record.captures_count}")
                cnt = record.captures_count
        print(f"device {num} finish")
        record.flush()
        record.close()
        print(f"device {num} closed")
        print(f"{record.captures_count} frames written on {self.file_name}_{num}.mkv.")

    def stop(self):
        self.is_recording = False

 
      
if __name__ == "__main__":
    recorder = firebase_recorder.Recorder()

    while True:
        try:
            print("recording")
        except KeyboardInterrupt:
            print("CTRL-C pressed. Exiting.")
            recorder.stop()
            break
