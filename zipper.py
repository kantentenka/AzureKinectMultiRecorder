from glob import glob
import time
import os
import threading
from subprocess import Popen

filename = ""
latest = ""
is_zipping = False
zipping_files = []
#todo ctrl-c で止めると圧縮されず元ファイルが消される問題
def zip_on_commandline(full_name,path):
    global zipping_files
    start = time.time()
    process=Popen(["7z","a",f"D:/NICT/{full_name}.7z",f"./record/{full_name}" ],shell = True)
    
    process.wait()
    size = 0
    while True:
        if size ==os.path.getsize(f"D:/NICT/{full_name}.7z") and size > 1000:
            time.sleep(1)
            os.remove(f"./record/{full_name}")
            print(f"{full_name} was zipped in {time.time() - start} s")
            zipping_files.remove(path)   
            
            print(f"./record/{full_name} was removed")
            break
        else:
            size = os.path.getsize(f"D:/NICT/{full_name}.7z")
            print(f"{full_name} {size}")
            time.sleep(1)


while True:
    files = glob("./record/*.mkv")
    files.sort(key=os.path.getmtime)
    
    if len(files)==0:
        print("there is no mkv")
        time.sleep(1)
    elif len(zipping_files) >=4:
        #print("4 threads are running")
        time.sleep(1)
    else:
        target = ""
        for i in files:
            if i not in zipping_files:
                target = i
                break
        if target=="":
            #print("all files are zipping")
            time.sleep(1)
        else:
            #print(target.split("\\"))
            filesize = os.path.getsize(target)
            #print(filesize)
            time.sleep(0.5)
            #print(os.path.getsize(target))
            #ファイルサイズが変わらないかつファイル生成直後でない
            if filesize ==  os.path.getsize(target) and filesize>100000:
                zipping_files.append(target)
                thread = threading.Thread(target=lambda : zip_on_commandline(target.split("\\")[1],target))#,daemon=True)
                thread.start()   
        
