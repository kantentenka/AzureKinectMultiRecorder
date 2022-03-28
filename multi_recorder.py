import cv2
import numpy as np

import pyk4a
from helpers import colorize
from pyk4a import Config, PyK4A, connected_device_count, PyK4ARecord

import threading
import time
import datetime

#import zipfile

import subprocess
from subprocess import Popen

import os


def cnt_device():
    cnt = connected_device_count()
    
    print(f"{cnt} device(s) connected")
    return cnt

is_recording = False

class Recorder():
    def __init__(self,is_remove=True):
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

        self.zipping_files = []
        self.is_remove = is_remove
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


    def recorder(self,file_name,k4a,record,device_num,file_num):
        cnt = 0
        print(f"device {device_num} file {file_num} record start")
        #while self.is_recording:
        #for i in range(150):
        for i in range(15*20):
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
        full_name = f"./{file_name}_{device_num}_{file_num}.mkv"
        print(f"{record.captures_count} frames written on {file_name}_{device_num}_{file_num}")
        record.flush()
        record.close()
        del record

        
        #self.zipper(f"{file_name}_{device_num}_{file_num}")

        self.zip_on_commandline(full_name)
    def stop(self):
        print("stop recording")
        self.is_recording = False
    def zip_on_commandline(self,full_name):
        self.zipping_files.append(full_name)
        start = time.time()
        #subprocess.run(["powershell","compress-archive",f"./record/{fullname}",f"D:/NICT/{fullname}.zip" ])
        process=Popen(["powershell","compress-archive",f"./record/{full_name}",f"D:/NICT/{full_name}.zip" ],shell = True)
        process.wait()
        print(f"{full_name} was zipped in {time.time() - start} s")
        self.zipping_files.remove(full_name)
        if self.is_remove:
            
            os.remove(f"./record/{full_name}")
            print(f"./record/{full_name} was removed")
    def zipper(self,full_name):
        self.start = time.time()
        print(f"{full_name} is zipping")
        with zipfile.ZipFile(f'D:/NICT/{full_name}.zip', 'w',
                     compression=zipfile.ZIP_DEFLATED,
                     compresslevel=9) as zf:
            zf.write(f'./record/{full_name}',f'{full_name}')
        print(f"{full_name} was zipped in {time.time() -self.start} s")
        if self.is_remove:
            os.remove(f"./record/{full_name}")
    def len_zip_proccess(self):
        
        for i in self.zipping_files:
            print(f'{i} is zipping')
        print()
        return len(self.zipping_files)



if __name__ == "__main__":
    recorder = Recorder(is_remove = True)
    import sys, signal
    import msvcrt
    def signal_handler(signal, frame):
        recorder.stop()
        print("\nprogram exiting gracefully\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    recorder.start()
    print("press escape to stop")
    while True:
        if msvcrt.kbhit() and msvcrt.getch() == chr(27).encode():
            print("escaped")
            recorder.stop()
            break
    
    #while recorder.len_zip_proccess():
    #    print(recorder.len_zip_proccess())
