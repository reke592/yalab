from globals import blacklist, lock, EVENT_STOP_BLACKLISTD_SERVICE, EVENT_FETCH_UPDATES, EVENT_APPLY_UPDATES, BLACKLIST_UPDATE_INTERVAL
import threading
import time
import sqlite3
import yadb

def fetchUpdates():
    t_elapsed = time.time() - _last_update
    if t_elapsed > BLACKLIST_UPDATE_INTERVAL or not _last_update:
        threading.Event.set(EVENT_FETCH_UPDATES)
        default_list, per_user = yadb.get_last_update()
        if len(default_list):
            applyUpdates(default_list)
        threading.Event.clear(EVENT_FETCH_UPDATES)


def applyUpdates(data=[]):
    try:
        threading.Event.set(EVENT_APPLY_UPDATES)
        print('acquiring lock')
        lock.acquire()
        print('updating blacklist')
        blacklist.include(data, yadb.done_update_blacklist_default)
        blacklist.compile()
        lock.release()
        print('released lock')
        threading.Event.clear(EVENT_APPLY_UPDATES)
    except Exception as e:
        print(e)
    finally:
        _tick_updates()

# called every successful updates
def _tick_updates():
    global _last_update
    _last_update = time.time()

# run on different thread
def service():
    yadb.init('app.db', create=True)
    print('started service blacklistd')
    while True:
        fetchUpdates()
        if threading.Event.is_set(EVENT_STOP_BLACKLISTD_SERVICE):
            break
        fetchUpdates()
        time.sleep(1)
    print('stopped blacklistd service')

def Server():
    global _last_update
    _last_update = 0.0
    return threading.Thread(target=service, name='blacklistd', daemon=True)