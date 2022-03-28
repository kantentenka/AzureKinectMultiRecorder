import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account
from glob import glob
import datetime

import multi_recorder
import threading
import time

cred = credentials.Certificate(f'{glob("./json/*json")[0]}')
firebase_admin.initialize_app(cred)

db = firestore.client()

f = open('config.txt', 'r')
data = f.read()
data=[i.split(",") for i in data.split("\n")]
f.close()
print(data)


doc_ref = db.collection(u'some_user')
doc_ref.add({
    u'datetime':datetime.datetime.now(),
    u'record': False,
    u'machine_id':data[0][1],
    u'connected_device_cnt':multi_recorder.cnt_device(),
    u'expect_connected_device_cnt':int(data[1][1]),
    u'comment':'device is started',
})

# Create an Event for notifying main thread.
callback_done = threading.Event()

# Create a callback on_snapshot function to capture changes


col_query = db.collection(u'some_user')
is_recording = False

recorder = multi_recorder.Recorder()
rec_start_time = 0
def on_snapshot(col_snapshot, changes, read_time):
    global is_recording,rec_start_time
    print(u'Callback received query snapshot.')
    print(u'Current cities in California:')
    query = col_query.order_by("datetime", direction=firestore.Query.DESCENDING).limit(1)
    docs = query.get()
    tdatetime = datetime.datetime.now()
    tstr = tdatetime.strftime('%Y%m%d_%H%M%S')
    #docsの中身は最新の一つのみ
    for doc in docs:
        print(f'{doc.id} => {doc.to_dict()}')
        if doc.to_dict()["record"] == True and is_recording == False:
            rec_start_time = time.time()
            recorder.start(file_name=tstr)
            
        elif doc.to_dict()["record"] == False:
            recorder.stop()
        is_recording = doc.to_dict()["record"]

    callback_done.set()


def count_one_hour():
    global is_recording,rec_start_time
    if is_recording:
        if time.time() -rec_start_time >60*60:
            doc_ref.add({
                u'datetime':datetime.datetime.now(),
                u'record': False,
                u'machine_id':data[0][1],
                u'connected_device_cnt':multi_recorder.cnt_device(),
                u'expect_connected_device_cnt':int(data[1][1]),
                u'comment':"record stop because one hour hass passed"
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
    recorder.start()
    print("press escape to stop")
    while True:
        if msvcrt.kbhit() and msvcrt.getch() == chr(27).encode():
            print("escaped")
            recorder.stop()
            break
        time.sleep(0.5)
        
        count_one_hour()
