import tkinter as tk
from tkinter import ttk, messagebox
from db import init_db
from auth import register_user, login_user
from diary.auth import hash_password
from utils import get_subjects, get_grades_by_student, get_avg_by_subject
import sqlite3
from datetime import datetime

current_user = None

root = tk.Tk()
root.title("Электронный дневник")
root.geometry("600x450")

def register(win):
    def submit():
        fio = entry_fio.get().strip()
        group = entry_group.get().strip()
        password = entry_password.get().strip()

        if not fio or not group or not password or not role_var.get():
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены и роль выбрана")
            return

        # Попытка регистрации пользователя
        result = register_user(fio, group, role_var.get(), password)
        if "успешно зарегистрирован" in result:
            messagebox.showinfo("Успех", result)
            win.destroy()
        else:
            messagebox.showerror("Ошибка", result)

    tk.Label(win, text="ФИО:", width=50, height=2).pack()
    entry_fio = tk.Entry(win, width=50)
    entry_fio.pack()

    tk.Label(win, text="Группа:", width=50, height=2).pack()
    entry_group = tk.Entry(win, width=50)
    entry_group.pack()

    tk.Label(win, text="Пароль:", width=50, height=2).pack()
    entry_password = tk.Entry(win, show="*", width=50)
    entry_password.pack()

    role_var = tk.StringVar(value="student")  # Установка значения по умолчанию на "Ученик"
    tk.Radiobutton(win, text="Ученик", variable=role_var, value="student", width=50, height=2).pack()
    tk.Radiobutton(win, text="Учитель", variable=role_var, value="teacher", width=50, height=2).pack()
    tk.Radiobutton(win, text="Администратор", variable=role_var, value="admin", width=50, height=2).pack()

    tk.Button(win, text="Зарегистрироваться", command=submit, width=50, height=2).pack()

def create_initial_admin():
    admin_fio = "admin"
    admin_password = "admin"
    role = "admin"
    register_user(admin_fio, None, role, hash_password(admin_password))

create_initial_admin()

def login():
    global current_user
    fio = entry_login.get().strip()
    password = entry_password.get().strip()

    if not fio or not password:
        messagebox.showerror("Ошибка", "Введите ФИО и пароль")
        return

    user = login_user(fio, password)
    if user:
        current_user = user
        load_interface()
    else:
        messagebox.showerror("Ошибка", "Пользователь не найден или неверный пароль")


def load_interface():
    global current_user
    if current_user is None:
        messagebox.showerror("Ошибка", "Не удалось загрузить информацию о пользователе.")
        return

    role = current_user[3]

    if role == "admin":
        root.withdraw()  # Закрываем главное окно
        register(tk.Toplevel())  # Открываем окно регистрации
    else:
        root.withdraw()  # Скрываем главное окно
        full = tk.Toplevel()  # Создаем новое окно для студентов и учителей
        full.geometry("1000x600")

        if role == "student":
            display_student(full)  # Отобразить интерфейс для ученика
        elif role == "teacher":
            display_teacher(full)  # Отобразить интерфейс для учителя
        else:
            messagebox.showerror("Ошибка", "Неизвестная роль пользователя.")

def display_student(win):
    subjects = ["Все"] + get_subjects()
    sub_var = tk.StringVar(value="Все")

    tree = ttk.Treeview(win, columns=("Предмет", "Оценка", "Дата"), show="headings", height=10)
    tree.heading("Предмет", text="Предмет")
    tree.heading("Оценка", text="Оценка")
    tree.heading("Дата", text="Дата")

    def refresh_table():
        tree.delete(*tree.get_children())
        subject = subject_combobox.get()
        data = get_grades_by_student(current_user[0], subject if subject != "Все" else None)
        for subj, grade, date in data:
            tree.insert('', 'end', values=(subj, grade, date))

        # Средний балл
        if subject != "Все":
            avg = get_avg_by_subject(current_user[0], subject)
            avg_label.config(text=f"Средний балл по {subject}: {round(avg, 2) if avg else 'нет данных'}")
        else:
            avg_label.config(text="")

    def show_avg():
        subject = subject_combobox.get()
        if subject == "Все":
            messagebox.showinfo("Средний балл", "Выберите конкретный предмет")
            return
        avg = get_avg_by_subject(current_user[0], subject)
        messagebox.showinfo("Средний балл", f"{subject}: {round(avg, 2) if avg else 'нет данных'}")

    # Стили
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
    style.configure("Treeview", font=("Helvetica", 11), rowheight=25)

    # Интерфейс
    tk.Label(win, text="Выберите предмет:", font=("Helvetica", 12)).pack(pady=10)
    subject_combobox = ttk.Combobox(win, textvariable=sub_var, values=subjects)
    subject_combobox.bind("<<ComboboxSelected>>", lambda _: refresh_table())
    subject_combobox.pack(pady=5)
    tree.pack(fill='both', expand=True, padx=10, pady=10)

    avg_label = tk.Label(win, font=("Helvetica", 12, "italic"))
    avg_label.pack(pady=10)

    tk.Button(win, text="Средний балл", command=show_avg).pack(pady=5)

    refresh_table()

def display_teacher(win):
    tk.Label(win, text="Группа", width=40, height=2, font=14).pack()
    group_var = tk.StringVar()
    group_combo = ttk.Combobox(win, textvariable=group_var, state="readonly", width=40, height=3, font=14)
    group_combo.pack()

    tk.Label(win, text="ФИО ученика", width=40, height=2, font=14).pack()
    student_var = tk.StringVar()
    student_combo = ttk.Combobox(win, textvariable=student_var, state="readonly", width=40, height=3, font=14)
    student_combo.pack()

    # Обновить список групп
    def update_groups():
        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT DISTINCT group_name FROM users WHERE role='student'")
        groups = [g[0] for g in c.fetchall()]
        conn.close()

        group_combo['values'] = groups
        if groups:
            group_combo.current(0)  # Устанавливаем первую группу как активную
            update_students_by_group()

    # Обновление списка студентов в зависимости от выбранной группы
    def update_students_by_group(*args):
        selected_group = group_combo.get()
        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT fio FROM users WHERE role='student' AND group_name=?", (selected_group,))
        students = [s[0] for s in c.fetchall()]
        conn.close()

        student_combo['values'] = students
        if students:
            student_var.set(students[0])  # Выбор первого студента по умолчанию
        else:
            student_var.set("")

    # Привязываем функцию для обновления студентов к выбору группы
    group_combo.bind("<<ComboboxSelected>>", update_students_by_group)
    group_var.trace_add("write", update_students_by_group)
    update_groups()

    # Список предметов
    tk.Label(win, text="Предмет", width=40, height=2, font=14).pack()
    subject_var = tk.StringVar()
    subject_combo = ttk.Combobox(win, textvariable=subject_var, state="readonly", width=40, height=3, font=14)
    subject_combo.pack()

    def update_subjects():
        subjects = get_subjects()
        subject_combo['values'] = subjects
        if subjects:
            subject_var.set(subjects[0])
        else:
            subject_var.set("")

    update_subjects()

    # Новый предмет
    tk.Label(win, text="Новый предмет (если нужно):", width=40, height=2, font=14).pack()
    entry_new_subject = tk.Entry(win, width=40, font=14)
    entry_new_subject.pack()

    def add_new_subject():
        new_subj = entry_new_subject.get().strip()
        if not new_subj:
            messagebox.showwarning("Пусто", "Введите название предмета")
            return
        subjects = get_subjects()
        if new_subj in subjects:
            messagebox.showinfo("Инфо", "Такой предмет уже существует")
        else:
            conn = sqlite3.connect("diary.db")
            c = conn.cursor()
            c.execute("INSERT INTO subjects (name) VALUES (?)", (new_subj,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Ок", f"Предмет '{new_subj}' добавлен")
            update_subjects()

    tk.Button(win, text="Добавить предмет", command=add_new_subject, width=30, height=2, font=14).pack(pady=8)

    # Ввод оценки
    tk.Label(win, text="Оценка (1-5)", font=14, width=40, height=2).pack()
    entry_grade = tk.Entry(win, width=40, font=14)
    entry_grade.pack()

    def is_valid_date(date_str):
        try:
            datetime.strptime(date_str, "%d-%m-%Y")
            return True
        except ValueError:
            return False

    tk.Label(win, text="Дата оценки (дд-мм-гггг)", font=14, width=40, height=2).pack()
    entry_date = tk.Entry(win, width=40, font=14)
    entry_date.pack()

    def submit_grade():
        fio = student_combo.get()
        subject = subject_combo.get()
        try:
            grade = int(entry_grade.get())
            if not (1 <= grade <= 5):
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Оценка должна быть числом от 1 до 5")
            return

        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE fio = ? AND role = 'student'", (fio,))
        stu = c.fetchone()
        if stu:
            date_str = entry_date.get().strip()
            if not is_valid_date(date_str):
                messagebox.showerror("Ошибка", "Введите корректную дату в формате дд-мм-гггг")
                return
            c.execute(
                "INSERT INTO grades (student_id, subject, grade, date) VALUES (?, ?, ?, ?)",
                (stu[0], subject, grade, date_str))
            conn.commit()
            messagebox.showinfo("Ок", "Оценка добавлена")
        else:
            messagebox.showerror("Ошибка", "Ученик не найден")
        conn.close()

    def update_stu_id(*args):
        global stu_id
        fio = student_combo.get()
        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE fio = ? AND role = 'student'", (fio,))
        stu = c.fetchone()
        stu_id = stu[0] if stu else None  # Обновляем значение stu_id в зависимости от выбора

        conn.close()

    def show_avg():
        subject = subject_combo.get()
        if stu_id is not None:
            conn = sqlite3.connect("diary.db")
            c = conn.cursor()
            c.execute("SELECT AVG(grade) FROM grades WHERE student_id=? AND subject=?", (stu_id, subject))
            avg = c.fetchone()[0]
            messagebox.showinfo("Средний балл",
                                f"{student_combo.get()} по {subject}: {round(avg, 2) if avg else 'нет данных'}")
            conn.close()
        else:
            messagebox.showwarning("Ошибка", "Выберите студента для расчета среднего балла.")

    # Привязать обновление студента к изменению в student_combo
    student_combo.bind("<<ComboboxSelected>>", update_stu_id)

    tk.Button(win, text="Добавить", command=submit_grade, height=2, width=30, font=14).pack(pady = 8)
    tk.Button(win, text="Средний балл", command=show_avg, height=2, width=30, font=14).pack(pady = 8)

tk.Label(root, text="Введите ФИО и пароль для входа:", font=14).pack(pady=10)
entry_login = tk.Entry(root, width=40, font=14)
entry_login.pack(pady=5)
entry_password = tk.Entry(root, width=40, show='*', font=14)
entry_password.pack(pady=5)

tk.Button(root, text="Войти", command=login, width=20, height=2).pack(pady=10)

init_db()

root.mainloop()