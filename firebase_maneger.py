import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore,storage

# Use a service account
from glob import glob
import datetime

import multi_recorder
import threading
import time

import cv2
import io

#WARING:スリープするとwi-fi接続が途切れてエラーになります
#スリープしない設定にしてください


cred = credentials.Certificate(f'{glob("./json/*json")[0]}')
firebase_admin.initialize_app(cred,{"storageBucket":"azurekinetrecorder.appspot.com"})



db = firestore.client()
bucket = storage.bucket()

f = open('config.txt', 'r')
print(type(f))
data = f.read()
data=[i.split(",") for i in data.split("\n")]
f.close()
print(data)


doc_ref = db.collection(u'some_user')
doc_ref.add({
    u'datetime':datetime.datetime.now()-datetime.timedelta(hours=9),
    u'record': False,
    u'machine_id':data[0][1],
    u'connected_device_cnt':multi_recorder.cnt_device(),
    u'expect_connected_device_cnt':int(data[1][1]),
    u'comment':'device is started',
    u'screenshot':False,
    u'screenshotname':""
})

doc_imu_ref = db.collection(u'some_user_imu')

# Create an Event for notifying main thread.
callback_done = threading.Event()

# Create a callback on_snapshot function to capture changes


col_query = db.collection(u'some_user')
is_recording = False
is_first_read = True

recorder = multi_recorder.Recorder()
rec_start_time = 0

def add_imu(imu):
    for imu_i in imu.values():
        print(imu_i)
        imu_i["machine_id"] = data[0][1]
            
        doc_imu_ref.add(imu_i)

def on_snapshot(col_snapshot, changes, read_time):
    global is_recording,rec_start_time,is_first_read
    print(u'Callback received query snapshot.')
    print(u'Current cities in California:')
    query = col_query.order_by("datetime", direction=firestore.Query.DESCENDING).limit(1)
    docs = query.get()
    tdatetime = datetime.datetime.now()
    tstr = tdatetime.strftime('%Y%m%d_%H%M%S')
    for doc in docs:
        print(f'{doc.id} => {doc.to_dict()}')
        if is_first_read:
            is_first_read = False
            break
        if doc.to_dict()["record"] == True and is_recording == False:
            rec_start_time = time.time()
            add_imu(recorder.get_imu())
            recorder.start(file_name=tstr)
            
        elif doc.to_dict()["record"] == False:
            add_imu(recorder.get_imu())
            recorder.stop()
        if doc.to_dict()["screenshot"]:
            cap = recorder.get_captures()
            if cap:
                content_type = "image/png"
                tdatetime = datetime.datetime.now()
                tstr = tdatetime.strftime('%Y%m%d_%H%M%S')
                for dict_key,dict_item in cap.items():
                    firename = f"{tstr}_{data[0][1]}_{dict_key}.png"
                    blob = bucket.blob(firename)
                    is_success,buffer = cv2.imencode(".png",dict_item)
                    io_buf= io.BytesIO(buffer)
                    
                    blob.upload_from_file(io_buf,content_type=content_type)
                    doc_ref = db.collection(u'some_user_capture')
                    doc_ref.add({
                        u'datetime':datetime.datetime.now()-datetime.timedelta(hours=9),
                        u'filename':firename,
                        u'devicestate':f"{data[0][1]}_{dict_key}"
                    })
        is_recording = doc.to_dict()["record"]

    callback_done.set()


def count_one_hour():
    global is_recording,rec_start_time
    if is_recording:
        if time.time() -rec_start_time >60*60:
            doc_ref.add({
                u'datetime':datetime.datetime.now()-datetime.timedelta(hours=9),
                u'record': False,
                u'machine_id':data[0][1],
                u'connected_device_cnt':multi_recorder.cnt_device(),
                u'expect_connected_device_cnt':int(data[1][1]),
                u'comment':"record stop because one hour hass passed",
                u'screenshot':False,
                u'screenshotname':""
            })
            is_recording = False
        
if __name__ == "__main__":
    
    # Watch the collection query
    query_watch = col_query.on_snapshot(on_snapshot)
    
    import sys, signal
    import msvcrt
    #ctrl-cで呼び出される関数
    def signal_handler(signal, frame):
        recorder.stop()
        print("\nprogram exiting gracefully\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    #recorder.start()
    print("press escape to stop")
    while True:
        if msvcrt.kbhit() and msvcrt.getch() == chr(27).encode():
            print("escaped")
            recorder.stop()
            break
        time.sleep(0.5)
        
        count_one_hour()
