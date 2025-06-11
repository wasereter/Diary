import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(fio, group_name, role, password):
    conn = sqlite3.connect("diary.db")
    c = conn.cursor()

    # Проверка на существование пользователя
    c.execute("SELECT COUNT(*) FROM users WHERE fio = ?", (fio,))
    if c.fetchone()[0] > 0:
        conn.close()
        return "Пользователь с таким FIO уже зарегистрирован."

    # Добавление нового пользователя
    hashed_password = hash_password(password)
    c.execute("INSERT INTO users (fio, group_name, role, password) VALUES (?, ?, ?, ?)", (fio, group_name, role, hashed_password))
    conn.commit()
    conn.close()
    return "Пользователь успешно зарегистрирован."

def login_user(fio, password):
    conn = sqlite3.connect("diary.db")
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("SELECT * FROM users WHERE fio=? AND password=?", (fio, hashed_password))
    user = c.fetchone()
    conn.close()
    return user