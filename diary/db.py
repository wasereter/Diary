import sqlite3

def init_db():
    conn = sqlite3.connect("diary.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        fio TEXT NOT NULL,
        group_name TEXT,
        role TEXT CHECK(role IN ('teacher', 'student')) NOT NULL,
        password TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY,
        student_id INTEGER,
        subject TEXT NOT NULL,
        grade INTEGER CHECK(grade BETWEEN 1 AND 5),
        FOREIGN KEY(student_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()