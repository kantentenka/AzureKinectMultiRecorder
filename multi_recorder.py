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
from glob import glob

def cnt_device():
    cnt = connected_device_count()
    
    print(f"{cnt} device(s) connected")
    return cnt

is_recording = False

MAX_SAMPLES = 1000


def set_default_data(data):
    data["acc_x"] = MAX_SAMPLES * [data["acc_x"][-1]]
    data["acc_y"] = MAX_SAMPLES * [data["acc_y"][-1]]
    data["acc_z"] = MAX_SAMPLES * [data["acc_z"][-1]]
    data["gyro_x"] = MAX_SAMPLES * [data["acc_x"][-1]]
    data["gyro_y"] = MAX_SAMPLES * [data["acc_y"][-1]]
    data["gyro_z"] = MAX_SAMPLES * [data["acc_z"][-1]]

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
        
        
        self.captures = {}
        if not(self.is_k4a()):
            print("device init")
            self.init_device()
    def init_device(self):
        for i in range(self.cnt):
            try:
                print(i)
                
                self.k4a.append(PyK4A(
                    config = self.config,
                    device_id=i
                ))
                self.k4a[-1].start()

                # getters and setters directly get and set on device
                self.k4a[-1].whitebalance = 4500
                assert self.k4a[-1].whitebalance == 4500
                self.k4a[-1].whitebalance = 4510
                assert self.k4a[-1].whitebalance == 4510
            except Exception as e:
                print(e)
                self.k4a.pop()
        print(f"{len(self.k4a)} devices were init!")
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
        for i in range(len(self.k4a)):

            path = f"./record/{file_name}_{i}_0.mkv"
                
            rec = PyK4ARecord(
                device=self.k4a[i],
                config=self.config,
                path=path)
                          
            rec.create()  

            print(i)
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
            path = f"./record/{file_name}_{device_num}_{file_num+1}.mkv"
            next_rec = PyK4ARecord(
                    device=k4a,
                    config=self.config,
                    path=path)
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

        #self.zip_on_commandline(full_name)
    def stop(self):
        print("stop recording")
        self.is_recording = False
    def get_captures(self):
        for device_num,k4a_i in enumerate(self.k4a):
            capture = k4a_i.get_capture()
            print(capture.color.shape)
            size = capture.color.shape
            self.captures[device_num] = cv2.resize(capture.color,dsize=[size[1]//2,size[0]//2])
            
        if len(self.captures)!=0:
            return self.captures
        else:
            return None
    def get_imu(self):
        imu ={}
        for num,k4a_i in enumerate(self.k4a):
            sample = k4a_i.get_imu_sample()
            imu[num] = {}
            imu[num]["device_num"] = num
            imu[num]["acc_x"], imu[num]["acc_y"], imu[num]["acc_z"] = sample.pop("acc_sample")
            imu[num]["gyro_x"], imu[num]["gyro_y"], imu[num]["gyro_z"] = sample.pop("gyro_sample")
        return imu
    #使ていなzip圧縮関数　
    #圧縮する場合は別プロセスでzipper.pyを立ち上げること
    def zip_on_commandline(self,full_name):
        self.zipping_files.append(full_name)
        start = time.time()
        #subprocess.run(["powershell","compress-archive",f"./record/{fullname}",f"D:/NICT/{fullname}.zip" ])
        #process=Popen(["powershell","compress-archive",f"./record/{full_name}",f"D:/NICT/{full_name}.zip" ],shell = True)
        process=Popen(["7z","a",f"D:/NICT/{full_name}.zip",f"./record/{full_name}" ],shell = True)
        
        process.wait()
        print(f"{full_name} was zipped in {time.time() - start} s")
        self.zipping_files.remove(full_name)
        if self.is_remove:
            
            os.remove(f"./record/{full_name}")
            print(f"./record/{full_name} was removed")
            
    #使ていないzip圧縮関数　圧縮する場合は別プロセスでzipper.pyを立ち上げること

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
    recorder = Recorder(is_remove = False)
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
