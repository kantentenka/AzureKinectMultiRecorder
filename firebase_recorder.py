import cv2
import numpy as np

import pyk4a
from helpers import colorize
from pyk4a import Config, PyK4A, connected_device_count, PyK4ARecord

import threading
import time
import datetime

import zipfile

import subprocess
from subprocess import Popen

def cnt_device():
    cnt = connected_device_count()
    
    print(f"{cnt} device(s) connected")
    return cnt

is_recording = False

class Recorder():
    def __init__(self,remove=True):
        tdatetime = datetime.datetime.now()
        tstr = tdatetime.strftime('%Y%m%d_%H%M%S')
        self.prepared_name = tstr
        self.is_recording = False
        self.cnt = cnt_device()
        self.k4a = []
        self.record = []
        self.config=Config(            
            color_resolution=pyk4a.ColorResolution.RES_720P,
            depth_mode=pyk4a.DepthMode.NFOV_UNBINNED,
            synchronized_images_only=True,
            camera_fps=pyk4a.FPS.FPS_15,
        )

        self.remove = remove
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
    def start(self,file_name=""):
        if file_name == "":
            file_name = self.prepared_name
        self.is_recording = True
        if not self.cnt:
            print("No devices available")
            exit()
        
        if not(self.is_k4a()):
            print("device init")
            self.init_device()
        #self.record = []
        print(len(self.k4a)>0)
        for i in range(self.cnt):
            rec = PyK4ARecord(
                device=self.k4a[i],
                config=self.config,
                path=f"./record/{file_name}_{i}_0.mkv")
                          
            rec.create()  

    
            thread = threading.Thread(target=lambda : self.recorder(file_name,self.k4a[i],rec,i,0))#,daemon=True)
            thread.start()
            print(f"test{i}") 


    def recorder(self,file_name,k4a,record,device_num,file_num):
        cnt = 0
        print(f"device {device_num} file {file_num} record start")
        #while self.is_recording:
        #for i in range(150):
        for i in range(15*3):
            capture = k4a.get_capture()
            record.write_capture(capture)
            if not(self.is_recording):
                break
        #print(f"device {device_num} file {file_num} finish")

        if self.is_recording:
            next_rec = PyK4ARecord(
                    device=k4a,
                    config=self.config,
                    path=f"./record/{file_name}_{device_num}_{file_num+1}.mkv")
            next_rec.create()
            
            thread = threading.Thread(target=lambda : self.recorder(file_name,k4a,next_rec,device_num,file_num+1))#,daemon=True)
            thread.start()
        

        #print(f"device {device_num} file {file_num} closed")
        fullname = f"./{file_name}_{device_num}_{file_num}.mkv"
        print(f"{record.captures_count} frames written on {file_name}_{device_num}_{file_num}")
        record.flush()
        record.close()
        del record
        #subprocess.run(["powershell","compress-archive",f"./record/{fullname}",f"D:/NICT/{fullname}.zip" ])
        Popen(["powershell","compress-archive",f"./record/{fullname}",f"D:/NICT/{fullname}.zip" ],shell = True)
        #self.zip(f"{file_name}_{device_num}_{file_num}")

        
    def stop(self):
        self.is_recording = False

    def zip(self,file_name):
        self.start = time.time()
        print(f"{file_name} is zipping")
        with zipfile.ZipFile(f'D:/NICT/{file_name}.zip', 'w',
                     compression=zipfile.ZIP_DEFLATED,
                     compresslevel=9) as zf:
            zf.write(f'./record/{file_name}.mkv',f'{file_name}.mkv')
        print(f"{file_name} was zipped in {time.time() -self.start} s")
        if self.remove:
            pass



if __name__ == "__main__":
    recorder = Recorder(remove = False)
    import sys, signal
    def signal_handler(signal, frame):
        recorder.stop()
        print("\nprogram exiting gracefully")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    recorder.start()
    while True:
        pass
