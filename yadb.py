import os
import sqlite3
import time


def create_connection(path, create=False):
    _conn = None
    db_exist_before = os.path.exists(path)
    if not db_exist_before and not create:
        raise ValueError('database not found')
    elif not db_exist_before and create:
        _conn = sqlite3.connect(path)
        print('created new database file', os.path.basename(path))
    else:
        print('found database', os.path.basename(path))
        _conn = sqlite3.connect(path)
    return _conn


def db_schema():
    _blacklist_default = '''
        CREATE TABLE IF NOT EXISTS _blacklist_default(
            domain VARCHAR(60) UNIQUE,
            is_enabled BOOLEAN DEFAULT TRUE,
            updated DATETIME DEFAULT (STRFTIME('%d-%m-%Y %H:%M', 'NOW', 'localtime'))
        )
    '''
    _blocking_per_client = '''
        CREATE TABLE IF NOT EXISTS _blocking_per_client(
            fk_client INT,
            domain VARCHAR(60),
            is_enabled BOOLEAN DEFAULT TRUE,
            updated DATETIME DEFAULT (STRFTIME('%d-%m-%Y %H:%M', 'NOW', 'localtime'))
        )
    '''
    # temporary table to store domain blockings needed to update
    # after the update takes effect on dnsprox, delete db contents.
    _tmp_blacklist_default = '''
        CREATE TABLE IF NOT EXISTS _tmp_blacklist_default(
            domain VARCHAR(60) UNIQUE,
            is_enabled BOOLEAN DEFAULT TRUE,
            updated DATETIME DEFAULT (STRFTIME('%d-%m-%Y %H:%M', 'NOW', 'localtime'))
        )
    '''
    _tmp_blocking_per_client = '''
        CREATE TABLE IF NOT EXISTS _tmp_blocking_per_client(
            fk_client INT,
            domain VARCHAR(60),
            is_enabled BOOLEAN DEFAULT TRUE,
            updated DATETIME DEFAULT (STRFTIME('%d-%m-%Y %H:%M', 'NOW', 'localtime'))
        )
    '''
    # create client script to listen on server socket X (where X is also used for broadcast)
    # on-connect: fetch _blacklist_per_client
    _clients_online = '''
        CREATE TABLE IF NOT EXISTS _clients_online(
            ip_addr VARCHAR(15),
            hostname VARCHAR(60),
            is_online BOOLEAN,
            updated DATETIME DEFAULT (STRFTIME('%d-%m-%Y %H:%M', 'NOW', 'localtime'))
        )
    '''
    # trigger configurations
    _def_blacklist_trig_aft = '''
        CREATE TRIGGER IF NOT EXISTS "aft_blacklist_default_{0}" AFTER {0} ON _blacklist_default
        BEGIN
        INSERT into _tmp_blacklist_default(domain, is_enabled) values({1}, {2});
        END;
    '''
    _per_client_trig_aft = '''
        CREATE TRIGGER IF NOT EXISTS "aft_blocking_per_client_{0}" AFTER {0} ON _blocking_per_client
        BEGIN
        INSERT into _tmp_blocking_per_client(fk_client, domain, is_enabled) values({1}, {2}, {3});
        END;
    '''
    # list of queries
    return [
        _blacklist_default,
        _tmp_blacklist_default,
        _blocking_per_client,
        _tmp_blocking_per_client,
        _clients_online,
        _def_blacklist_trig_aft.format(
            'UPDATE', 'NEW.domain', 'NEW.is_enabled'),
        _def_blacklist_trig_aft.format(
            'INSERT', 'NEW.domain', 'NEW.is_enabled'),
        _def_blacklist_trig_aft.format('DELETE', 'OLD.domain', 'False'),
        _per_client_trig_aft.format(
            'UPDATE', 'NEW.fk_client', 'NEW.domain', 'NEW.is_enabled'),
        _per_client_trig_aft.format(
            'INSERT', 'NEW.fk_client', 'NEW.domain', 'NEW.is_enabled'),
        _per_client_trig_aft.format(
            'DELETE', 'OLD.fk_client', 'OLD.domain', 'False')
    ]

# create db


def init_schema():
    with conn:
        cursor = conn.cursor()
        for query in db_schema():
            cursor.execute(query)


def is_connected():
    return type(conn) is not type(None)


def disconnect():
    print('closing database connection')
    try:
        conn.close()
        print('database connection closed')
        return 0
    except Exception as e:
        print('something went wrong when closing database connection')
        print(e)
        return 1

# ----------- DB TRANSACTIONS


def show_clients():
    with conn:
        cursor = conn.cursor()
        q = 'SELECT * from _clients_online WHERE is_online = True'
        return cursor.execute(q).fetchall()

# fetch last updated records


def get_last_update():
    with conn:
        cursor = conn.cursor()
        q1 = 'SELECT rowid, domain, is_enabled FROM _tmp_blacklist_default'
        q2 = 'SELECT rowid, domain, is_enabled FROM _blocking_per_client'
        return [
            cursor.execute(q1).fetchall(),
            cursor.execute(q2).fetchall()
        ]

# fetch default blacklist


def get_default_list():
    with conn:
        cursor = conn.cursor()
        q = 'SELECT rowid, domain, is_enabled FROM _blacklist_default'
        return cursor.execute(q).fetchall()

# remove applied updates


def _done_updates(tbl, rowid=[]):
    try:
        with conn:
            cursor = conn.cursor()
            if not tbl:
                raise ValueError('unknown table', tbl)
            ids = ','.join(rowid)
            q = 'DELETE from _tmp{0} WHERE rowid in ({1})'
            cursor.execute(q.format(tbl, ids))
            print('updates removed in queue')
    except Exception as e:
        print('something went wrong when updating the database on done_updates')
        print('Exception:', e)


def done_update_blacklist_default(rowid=[]):
    _done_updates('_blacklist_default', rowid)


def done_update_blocking_per_client(rowid=[]):
    _done_updates('_blocking_per_client', rowid)

# ------------- DB


def init(path, create=False):
    global conn
    conn = create_connection(path, create)
    init_schema()  # always create db schema if not exist
