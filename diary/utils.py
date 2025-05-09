import sqlite3

def get_subjects():
    conn = sqlite3.connect("diary.db")
    c = conn.cursor()
    c.execute("SELECT name FROM subjects")
    subjects = [row[0] for row in c.fetchall()]
    conn.close()
    return subjects

def subject_exists(subject):
    conn = sqlite3.connect("diary.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM subjects WHERE subject=? LIMIT 1", (subject,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def get_grades_by_student(student_id, subject_filter=None):
    conn = sqlite3.connect("diary.db")
    c = conn.cursor()
    if subject_filter:
        c.execute("SELECT subject, grade, date FROM grades WHERE student_id=? AND subject=?", (student_id, subject_filter))
    else:
        c.execute("SELECT subject, grade, date FROM grades WHERE student_id=?", (student_id,))
    data = c.fetchall()
    conn.close()
    return data

def get_avg_by_subject(student_id, subject):
    conn = sqlite3.connect("diary.db")
    c = conn.cursor()
    c.execute("SELECT AVG(grade) FROM grades WHERE student_id=? AND subject=?", (student_id, subject))
    avg = c.fetchone()[0]
    conn.close()
    return round(avg, 2) if avg else None