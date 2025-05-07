import tkinter as tk
from tkinter import ttk, messagebox
from db import init_db
from auth import register_user, login_user
from utils import get_subjects, get_grades_by_student, get_avg_by_subject
import sqlite3



current_user = None


def register():
    def submit():
        fio = entry_fio.get().strip()
        group = entry_group.get().strip()
        password = entry_password.get().strip()

        if not fio or not group or not password:
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены")
            return

        # Попытка регистрации пользователя
        if register_user(fio, group, role_var.get(), password):
            messagebox.showinfo("Успех", "Пользователь зарегистрирован")
            top.destroy()
        else:
            messagebox.showerror("Ошибка",
                                 "Не удалось зарегистрировать пользователя. Возможно, пользователь с таким ФИО уже существует.")

    top = tk.Toplevel()
    top.title("Регистрация")
    tk.Label(top, text="ФИО:").pack()
    entry_fio = tk.Entry(top)
    entry_fio.pack()

    tk.Label(top, text="Группа:").pack()
    entry_group = tk.Entry(top)
    entry_group.pack()

    tk.Label(top, text="Пароль:").pack()
    entry_password = tk.Entry(top, show="*")
    entry_password.pack()

    role_var = tk.StringVar(value="student")
    tk.Radiobutton(top, text="Ученик", variable=role_var, value="student").pack()
    tk.Radiobutton(top, text="Учитель", variable=role_var, value="teacher").pack()

    tk.Button(top, text="Зарегистрироваться", command=submit).pack()


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
    global current_user  # Обратите внимание, что мы используем глобальную переменную
    if current_user is None:
        messagebox.showerror("Ошибка", "Не удалось загрузить информацию о пользователе.")
        return

    root.withdraw()  # Скрываем главное окно
    full = tk.Tk()
    full.geometry("600x400")

    role = current_user[3]  # Предполагаем, что роль пользователя хранится в четвертом элементе
    if role == "student":
        display_student(full)  # Отобразить интерфейс для ученика
    elif role == "teacher":
        display_teacher(full)  # Отобразить интерфейс для учителя
    else:
        messagebox.showerror("Ошибка", "Неизвестная роль пользователя.")  # Отображаем интерфейс для учителя

def display_student(win):
    subjects = ["Все"] + get_subjects()
    sub_var = tk.StringVar(value="Все")

    def refresh_table():
        tree.delete(*tree.get_children())
        subject = sub_var.get()
        data = get_grades_by_student(current_user[0], subject if subject != "Все" else None)
        for subj, grade in data:
            tree.insert('', 'end', values=(subj, grade))

        # Средний балл
        if subject != "Все":
            avg = get_avg_by_subject(current_user[0], subject)
            avg_label.config(text=f"Средний балл по {subject}: {round(avg, 2) if avg else 'нет данных'}")
        else:
            avg_label.config(text="")

    def show_avg():
        subject = sub_var.get()
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
    subject_menu = tk.OptionMenu(win, sub_var, *subjects, command=lambda _: refresh_table())
    subject_menu.pack()

    tree = ttk.Treeview(win, columns=("Предмет", "Оценка"), show="headings", height=10)
    tree.heading("Предмет", text="Предмет")
    tree.heading("Оценка", text="Оценка")
    tree.pack(fill='both', expand=True, padx=10, pady=10)

    avg_label = tk.Label(win, font=("Helvetica", 12, "italic"))
    avg_label.pack(pady=10)

    tk.Button(win, text="Средний балл", command=show_avg).pack(pady=5)

    refresh_table()


def display_teacher(win):
    tk.Label(win, text="ФИО ученика").pack()

    student_var = tk.StringVar()
    student_menu = tk.OptionMenu(win, student_var, "")
    student_menu.pack()

    group_var = tk.StringVar()  # Добавим выбор группы
    group_menu = tk.OptionMenu(win, group_var, "")
    group_menu.pack()

    # Функция для обновления списка студентов по группам
    def update_students():
        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT DISTINCT group_name FROM users WHERE role='student'")
        groups = [g[0] for g in c.fetchall()]
        conn.close()

        menu = group_menu["menu"]
        menu.delete(0, "end")
        for group in groups:
            menu.add_command(label=group, command=lambda value=group: group_var.set(value))
        if groups:
            group_var.set(groups[0])

    update_students()

    # Функция для обновления студентов в зависимости от выбранной группы
    def update_students_by_group():
        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT fio FROM users WHERE role='student' AND group_name=?", (group_var.get(),))
        students = [s[0] for s in c.fetchall()]
        conn.close()

        menu = student_menu["menu"]
        menu.delete(0, "end")
        for s in students:
            menu.add_command(label=s, command=lambda value=s: student_var.set(value))
        if students:
            student_var.set(students[0])

    group_var.trace("w", lambda *args: update_students_by_group())  # Обновление студентов при выборе группы

    # Обновление списка предметов
    tk.Label(win, text="Предмет").pack()
    subject_var = tk.StringVar()
    subject_menu = tk.OptionMenu(win, subject_var, "")
    subject_menu.pack()

    def update_subjects():
        subjects = get_subjects()
        menu = subject_menu["menu"]
        menu.delete(0, "end")
        for s in subjects:
            menu.add_command(label=s, command=lambda value=s: subject_var.set(value))
        if subjects:
            subject_var.set(subjects[0])

    update_subjects()

    # Добавление нового предмета
    tk.Label(win, text="Новый предмет (если нужно):").pack()
    entry_new_subject = tk.Entry(win)
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
            # Добавляем предмет в базу данных
            conn = sqlite3.connect("diary.db")
            c = conn.cursor()
            c.execute("INSERT INTO grades (subject) VALUES (?)", (new_subj,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Ок", f"Предмет '{new_subj}' добавлен")
            update_subjects()  # Обновляем список предметов

    tk.Button(win, text="Добавить предмет", command=add_new_subject).pack(pady=5)

    # Оценка студента
    tk.Label(win, text="Оценка (1-5)").pack()
    entry_grade = tk.Entry(win)
    entry_grade.pack()

    def submit_grade():
        fio = student_var.get()
        subject = subject_var.get()
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
            # Записываем оценку в базу
            c.execute("INSERT INTO grades (student_id, subject, grade) VALUES (?, ?, ?)", (stu[0], subject, grade))
            conn.commit()
            messagebox.showinfo("Ок", "Оценка добавлена")
        else:
            messagebox.showerror("Ошибка", "Ученик не найден")
        conn.close()

    # Показать средний балл
    def show_avg():
        fio = student_var.get()
        subject = subject_var.get()
        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE fio = ? AND role = 'student'", (fio,))
        stu = c.fetchone()
        if stu:
            c.execute("SELECT AVG(grade) FROM grades WHERE student_id=? AND subject=?", (stu[0], subject))
            avg = c.fetchone()[0]
            messagebox.showinfo("Средний балл", f"{fio} по {subject}: {round(avg, 2) if avg else 'нет данных'}")
        conn.close()

    # Кнопки
    tk.Button(win, text="Добавить", command=submit_grade).pack()
    tk.Button(win, text="Средний балл", command=show_avg).pack()

root = tk.Tk()
root.title("Электронный дневник")
root.geometry("450x350")

tk.Label(root, text="Введите ФИО и пароль для входа:").pack(pady=10)
entry_login = tk.Entry(root, width=40)
entry_login.pack(pady=5)
entry_password = tk.Entry(root, width=40, show='*')
entry_password.pack(pady=5)

tk.Button(root, text="Войти", command=login, width=20, height=2).pack(pady=10)
tk.Button(root, text="Регистрация", command=register, width=20, height=2).pack()

init_db()

root.mainloop()
