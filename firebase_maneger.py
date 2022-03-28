import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account
from glob import glob
import datetime

import firebase_recorder
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
    u'connected_device_cnt':firebase_recorder.cnt_device(),
    u'expect_connected_device_cnt':int(data[1][1])
})

# Create an Event for notifying main thread.
callback_done = threading.Event()

# Create a callback on_snapshot function to capture changes


col_query = db.collection(u'some_user')
is_recording = False

recorder = firebase_recorder.Recorder()

def on_snapshot(col_snapshot, changes, read_time):
    global is_recording
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
            recorder.start(tstr)
        elif doc.to_dict()["record"] == False:
            recorder.stop()
        is_recording = doc.to_dict()["record"]

    callback_done.set()


if __name__ == "__main__":
    
    # Watch the collection query
    query_watch = col_query.on_snapshot(on_snapshot)
    while True: 
        time.sleep(1)
