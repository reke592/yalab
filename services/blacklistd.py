from yaglobal import blacklist, lock, EVENT_STOP_BLACKLISTD_SERVICE, EVENT_FETCH_UPDATES, EVENT_APPLY_UPDATES, BLACKLIST_UPDATE_INTERVAL
import threading
import time
import sqlite3
import yadb


def fetchDefaultList():
    threading.Event.set(EVENT_FETCH_UPDATES)
    default_list = yadb.get_default_list()
    if len(default_list):
        applyUpdates(default_list)


def fetchUpdates():
    t_elapsed = time.time() - _last_update
    if t_elapsed > BLACKLIST_UPDATE_INTERVAL:
        threading.Event.set(EVENT_FETCH_UPDATES)
        default_list, per_user = yadb.get_last_update()
        if len(default_list):
            applyUpdates(default_list)
            print('done applying updates...')


def applyUpdates(data=[]):
    try:
        threading.Event.clear(EVENT_FETCH_UPDATES)
        threading.Event.set(EVENT_APPLY_UPDATES)
        print('acquiring lock')
        lock.acquire()
        print('updating blacklist')
        blacklist.include(data, yadb.done_update_blacklist_default)
        blacklist.compile()
        lock.release()
        print('released lock')
        # threading.Event.clear(EVENT_APPLY_UPDATES)
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
    print('started service blacklistd')
    yadb.init('app.db', create=True)
    fetchDefaultList()
    _tick_updates()
    while True:
        if threading.Event.is_set(EVENT_STOP_BLACKLISTD_SERVICE):
            break
        fetchUpdates()
        time.sleep(1)
    print('stopped blacklistd service')


def Server():
    return threading.Thread(target=service, name='blacklistd', daemon=True)
