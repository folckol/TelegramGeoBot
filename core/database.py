import sqlite3

with sqlite3.connect('database.db', check_same_thread=False) as connection:
    db = connection.cursor()

def create_table():
    db.execute('''CREATE TABLE IF NOT EXISTS admin (
        user_id INTEGER
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS location_search (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latitude TEXT,
        longitude TEXT
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS word (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS location_coworking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latitude TEXT,
        longitude TEXT
    )''')

    db.execute('''CREATE TABLE IF NOT EXISTS received (
        user_id INTEGER
    )''')

def insert_received(user_id):
    db.execute(f"INSERT INTO received (user_id) VALUES (?)", (user_id,))
    connection.commit()

def insert_location(latitude, longitude, mode):
    if mode == 'location_coworking':
        db.execute(f"INSERT INTO '{mode}' ('latitude','longitude') VALUES (?, ?)", (latitude, longitude,))
        connection.commit()
    elif mode == 'location_search':
        db.execute(f'UPDATE {mode} SET latitude = "{latitude}"')
        db.execute(f'UPDATE {mode} SET longitude = "{longitude}"')
        connection.commit()

def delete_location(id, mode):
    db.execute(f'''DELETE FROM {mode} WHERE id = {id}''')
    connection.commit()

def insert_admin(user_id):
    db.execute(f"INSERT INTO admin ('user_id') VALUES (?)", (user_id,))
    connection.commit()

def delete_admin(user_id):
    db.execute(f'''DELETE FROM admin WHERE user_id = "{user_id}" ''')
    connection.commit()

def delete_word(id):
    db.execute(f'''DELETE FROM word WHERE id = "{id}" ''')
    connection.commit()

def select_location(mode):
    return db.execute(f'''SELECT * FROM {mode}''').fetchall()

def select_location_where(mode, where_id):
    return db.execute(f'''SELECT * FROM {mode} WHERE id = {where_id}''').fetchall()

def select_admin():
    return db.execute(f'''SELECT user_id FROM admin''').fetchall()

def select_received():
    return db.execute(f'''SELECT user_id FROM received''').fetchall()

def insert_word(word):
    db.execute(f"INSERT INTO word ('word') VALUES (?)", (word, ))
    connection.commit()

def select_random_word():
    return db.execute(f'''SELECT * FROM word''').fetchall()

def where_select_random_word(id):
    return db.execute(f'''SELECT * FROM word WHERE id = {id}''').fetchall()
