#7zipで圧縮しています
#使う前に7zのpathを通してください

#FixMe:エラーで0kbのmkvファイルが生成されて放置されると圧縮できなくなります。

from glob import glob
import time
import os,sys,shutil
import threading
from subprocess import Popen
import msvcrt

filename = ""
latest = ""
is_zipping = False
zipping_files = []
#todo ctrl-c で止めると圧縮されず元ファイルが消される問題
def zip_on_commandline(full_name,path):
    global zipping_files
    start = time.time()
    extension = "zip"
    process=Popen(["7z","a",f"D:/NICT/{full_name}.{extension}",f"D:/record/{full_name}" ],shell = True)
    
    process.wait()
    zipping_files.remove(path)

"""
#ファイル削除の処理
#メインスレッドのzip化とファイル削除がかぶってエラーが生じることがあるから使わない
    size = 0
    while True:
        if size ==os.path.getsize(f"D:/NICT/{full_name}.{extension}") and size > 1000:
            time.sleep(1)
            os.remove(f"D:/record/{full_name}")
            print(f"{full_name} was zipped in {time.time() - start} s")
            zipping_files.remove(path)   
            
            print(f"D:/record/{full_name} was removed at {time.time()-start}")
            break
        else:
            size = os.path.getsize(f"D:/NICT/{full_name}.{extension}")
            print(f"{full_name} {size}")
            time.sleep(1)
"""

if len(glob("D:/record"))==0:
       print("there is no folder 'D:/record'")
       sys.exit()
while True:

    #escが押されたら終了
    if msvcrt.kbhit() and msvcrt.getch() == chr(27).encode():
        print("escaped")
        break

    #./recordに関する処理

    files = glob("./record/*.mkv")
    files.sort(key=os.path.getmtime)
    if len(files)==0:
        print("there is no mkv")
        time.sleep(1)

    else:
        target = files[0]
        
        print(target)
        
        filesize = os.path.getsize(target)
        #print(filesize)
        time.sleep(0.5)
        #targetのファイルサイズが0.5変わらないかつファイル生成直後でない
        #つまりファイルの書き込みが終了したとき、targetをD:recordに移動
        if filesize ==  os.path.getsize(target) and filesize>100000:
              shutil.move(target, 'D:/record')
        time.sleep(0.5)


    #D:/recordに関する処理
    Dfiles = glob("D:/record/*.mkv")
    Dfiles.sort(key=os.path.getmtime)

    #まだ圧縮されていないファイルのみを抽出
    ZipFolderFiles = [i.replace('.zip', '').split("\\")[-1] for i in glob("D:/NICT/*.zip")]

    Dfiles = [i for i in Dfiles if (i.split("\\")[-1] not in ZipFolderFiles)]

    if len(Dfiles)==0:
        if len(zipping_files): 
            pass
        else:
            for i in glob("D:/record/*.mkv"):
                
                os.remove(i)
    #同時に並行して処理するファイルの数
    elif len(zipping_files) >=3:
        #print("4 threads are running")
        time.sleep(1)
    else:
        target = ""
        for i in Dfiles:
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
                #D:/recod/xxx.mkvからxxx.mkvだけとって、別スレッドで圧縮する
                thread = threading.Thread(target=lambda : zip_on_commandline(target.split("\\")[1],target))#,daemon=True)
                thread.start()   
        
