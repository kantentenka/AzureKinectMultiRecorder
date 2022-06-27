from mimetypes import init
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

def get_device_num():
    cnt = connected_device_count()
    
    #print(f"{cnt} device(s) connected")
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
        self.cnt = get_device_num()
        self.k4a = {}
        self.record = []
        self.config=Config(            
            color_resolution=pyk4a.ColorResolution.RES_720P,
            depth_mode=pyk4a.DepthMode.NFOV_UNBINNED,
            synchronized_images_only=True,
            camera_fps=pyk4a.FPS.FPS_15,
        )
        self.enabletoUseDevices = {}
        
        self.captures = {}

        if not(self.is_k4a()):
            print("device init")
            self.init_device()

        thread = threading.Thread(target=self.DeviceMonitor,daemon=True)
        thread.start()


    def init_device(self):
        for i in range( get_device_num()):
            print(i)            
            self.k4a[i] = PyK4A(
                config = self.config,
                device_id=i
            )

    def is_k4a(self):
        return len(self.k4a)>0
    def enabletoStart(self):
        if get_device_num() == 0:
            print("nodevice is abailable")
            for i in self.enabletoUseDevices:
                self.enabletoUseDevices[i] = False
            return
        for i in range( get_device_num()):
            
            trystart = False
            trycapture = False
            try:
                self.k4a[i].open()
                print(f"device {i} can open")
                #trystart = True
            except pyk4a.errors.K4AException as e:
                print(e)
                print(f"device {i} was feild to open")
            try:
                if not(self.k4a[i].is_running): 
                    self.k4a[i].start()
                    print(f"device {i} can start")
                else:
                    print(f"device {i} is already started")
                trystart = True
            except pyk4a.errors.K4AException as e:
                print(e)
                print(f"device {i} was feild to start")
            try:
                self.k4a[i].get_capture()
                print(f"device {i} can get capture")
                trycapture = True
            except pyk4a.errors.K4AException as e:
                print(e)
                print(f"device {i} was feild to get capture")
            
            self.enabletoUseDevices[i] = trycapture 

            if self.is_recording == False:
                self.k4a[i].stop()
    def DeviceMonitor(self):
        # 録画中に新しいデバイスを追加しても認識はされません
        device_count = get_device_num()
        while True:
            if not(self.is_recording):
                if device_count<get_device_num():
                    self.init_device()
                self.enabletoStart()
            time.sleep(3)

    def start(self,file_name=""):
        if file_name == "":
            file_name = self.prepared_name
        self.is_recording = True
        if not get_device_num():
            print("No devices available")
            return 
        
        if not(self.is_k4a()):
            print("device init")
            self.init_device()
        #self.record = []
        print(len(self.k4a)>0)

        for num,i in self.k4a.items():
            
            path = f"./record/{file_name}_{num}_0.mkv"
            print(path)
            is_start = False
            while  is_start == False:
                try :
                    
                    rec = PyK4ARecord(
                        device=self.k4a[num],
                        config=self.config,
                        path=path)
                                
                    rec.create()
                    print(i)
                    thread = threading.Thread(target=lambda : self.recorder(file_name,self.k4a[num],rec,num,0))#,daemon=True)
                    thread.start()
                    is_start = True
                except pyk4a.errors.K4AException as e:
                    print("cant record")
                    print(e)
                    self.enabletoStart()


    def recorder(self,file_name,k4a,record,device_num,file_num):
        cnt = 0
        self.enabletoStart()

        print(f"device {device_num} file {file_num} record start")
        #while self.is_recording:
        #for i in range(150):
        for i in range(15*20):
            try:
                capture = k4a.get_capture()
                record.write_capture(capture)
                
                if not(self.is_recording):
                    break
            except  pyk4a.errors.K4AException as e:
                print (e)
                try:
                    record.flush()
                    record.close()
                except:
                    pass
                del record

                self.waitdevice(device_num)
                return 0
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
    def waitdevice(self,i):
        print("wait device")
        try:
            self.k4a[i].stop()
        #except pyk4a.errors.K4AException as e:
        #    print(e)
        #    print("stop dekinai")
        except:
            print("nazo error")
        try:
            self.k4a[i]._stop_imu()
        #except pyk4a.errors.K4AException as e:
        #    print(e)
         #   print("imu stop dekinai")
        except:
            print("imu nazo error")
            

        while True:
            self.enabletoStart()
            if self.enabletoUseDevices[i]:
                break
            print("hajimettenai")
            time.sleep(1)
        print("restart")
        self.start()
    def get_captures(self):

        onlycapture = self.is_recording
        self.is_recording = True
        self.enabletoStart()
        for device_num,k4a_i in self.k4a.items():
            if self.enabletoUseDevices[device_num]:
                capture = k4a_i.get_capture()
                print(capture.color.shape)
                size = capture.color.shape
                self.captures[device_num] = cv2.resize(capture.color,dsize=[size[1]//2,size[0]//2])
        self.is_recording = onlycapture
        self.enabletoStart()
            
        if len(self.captures)!=0:
            return self.captures
        else:
            return None
        
        
    
    def get_imu(self):
        onlycapture = self.is_recording
        self.is_recording = True
        self.enabletoStart()
        
        imu ={}
        for num,k4a_i in self.k4a.items():
            print(num,k4a_i)
            if self.enabletoUseDevices[num]:
                sample = k4a_i.get_imu_sample()
                imu[num] = {}
                imu[num]["device_num"] = num
                imu[num]["acc_x"], imu[num]["acc_y"], imu[num]["acc_z"] = sample.pop("acc_sample")
                imu[num]["gyro_x"], imu[num]["gyro_y"], imu[num]["gyro_z"] = sample.pop("gyro_sample")
        self.is_recording = onlycapture
        self.enabletoStart()
        
        return imu
    
    

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
