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
    win.title("Регистрация пользователя")
    win.geometry("500x550")
    win.configure(bg="#f9f9f9")
    win.resizable(False, False)

    form_frame = tk.Frame(win, padx=20, pady=20, bg="#f9f9f9")
    form_frame.pack(expand=True)

    tk.Label(form_frame, text="Регистрация", font=("Helvetica", 18, "bold"), bg="#f9f9f9").grid(row=0, column=0,
                                                                                                columnspan=2, pady=10)

    tk.Label(form_frame, text="ФИО:", font=("Helvetica", 12), bg="#f9f9f9").grid(row=1, column=0, sticky="e", pady=5)
    entry_fio = tk.Entry(form_frame, width=30, font=("Helvetica", 12))
    entry_fio.grid(row=1, column=1, pady=5)

    tk.Label(form_frame, text="Группа:", font=("Helvetica", 12), bg="#f9f9f9").grid(row=2, column=0, sticky="e", pady=5)
    entry_group = tk.Entry(form_frame, width=30, font=("Helvetica", 12))
    entry_group.grid(row=2, column=1, pady=5)

    tk.Label(form_frame, text="Пароль:", font=("Helvetica", 12), bg="#f9f9f9").grid(row=3, column=0, sticky="e", pady=5)
    entry_password = tk.Entry(form_frame, show="*", width=30, font=("Helvetica", 12))
    entry_password.grid(row=3, column=1, pady=5)

    tk.Label(form_frame, text="Роль:", font=("Helvetica", 12), bg="#f9f9f9").grid(row=4, column=0, sticky="ne", pady=10)
    role_var = tk.StringVar(value="student")
    role_frame = tk.Frame(form_frame, bg="#f9f9f9")
    role_frame.grid(row=4, column=1, sticky="w", pady=5)

    for text, value in [("Ученик", "student"), ("Учитель", "teacher"), ("Администратор", "admin")]:
        tk.Radiobutton(role_frame, text=text, variable=role_var, value=value, bg="#f9f9f9",
                       font=("Helvetica", 11)).pack(anchor="w")

    def submit():
        fio = entry_fio.get().strip()
        group = entry_group.get().strip()
        password = entry_password.get().strip()

        if not fio or not group or not password or not role_var.get():
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены и роль выбрана")
            return

        result = register_user(fio, group, role_var.get(), password)
        if "успешно зарегистрирован" in result:
            messagebox.showinfo("Успех", result)
            win.destroy()
        else:
            messagebox.showerror("Ошибка", result)

    tk.Button(form_frame, text="Зарегистрироваться", command=submit,
              font=("Helvetica", 12), bg="#4CAF50", fg="white", width=25).grid(row=5, column=0, columnspan=2, pady=20)

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

    root.withdraw()  # Скрыть главное окно

    if role == "admin":
        reg_win = tk.Toplevel()
        reg_win.title("Регистрация новых пользователей")
        reg_win.geometry("500x550+400+150")  # Центровка
        register(reg_win)

    elif role in ["student", "teacher"]:
        full = tk.Toplevel()
        full.title("Электронный дневник")
        full.geometry("1000x600+200+100")
        full.configure(bg="#f0f0f0")
        full.resizable(True, True)

        if role == "student":
            display_student(full)
        elif role == "teacher":
            display_teacher(full)
        else:
            messagebox.showerror("Ошибка", "Неизвестная роль пользователя.")

def display_student(win):
    subjects = ["Все"] + get_subjects()
    sub_var = tk.StringVar(value="Все")

    win.title("Просмотр оценок")
    win.configure(bg="#f0f0f0")

    # Стилизация Treeview
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview",
                    font=("Helvetica", 11),
                    rowheight=28,
                    background="#ffffff",
                    fieldbackground="#ffffff")
    style.configure("Treeview.Heading",
                    font=("Helvetica", 12, "bold"),
                    background="#e0e0e0",
                    relief="flat")

    top_frame = tk.Frame(win, bg="#f0f0f0")
    top_frame.pack(fill="x", padx=20, pady=10)

    tk.Label(top_frame, text="Предмет:", font=("Helvetica", 12), bg="#f0f0f0").pack(side="left", padx=(0, 10))
    subject_combobox = ttk.Combobox(top_frame, textvariable=sub_var, values=subjects, width=30, state="readonly")
    subject_combobox.pack(side="left")
    subject_combobox.bind("<<ComboboxSelected>>", lambda _: refresh_table())

    table_frame = tk.Frame(win, bg="#f0f0f0")
    table_frame.pack(fill="both", expand=True, padx=20, pady=10)

    tree = ttk.Treeview(table_frame, columns=("Предмет", "Оценка", "Дата"), show="headings")
    tree.heading("Предмет", text="Предмет")
    tree.heading("Оценка", text="Оценка")
    tree.heading("Дата", text="Дата")
    tree.column("Предмет", anchor="center", width=200)
    tree.column("Оценка", anchor="center", width=100)
    tree.column("Дата", anchor="center", width=150)

    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    bottom_frame = tk.Frame(win, bg="#f0f0f0")
    bottom_frame.pack(fill="x", padx=20, pady=10)

    avg_label = tk.Label(bottom_frame, font=("Helvetica", 12, "italic"), bg="#f0f0f0", anchor="w")
    avg_label.pack(side="left", fill="x", expand=True)

    tk.Button(bottom_frame, text="Показать средний балл", command= lambda: show_avg(),
              bg="#4CAF50", fg="white", font=("Helvetica", 11), width=25, height=1).pack(side="right")

    def refresh_table():
        tree.delete(*tree.get_children())
        subject = subject_combobox.get()
        data = get_grades_by_student(current_user[0], subject if subject != "Все" else None)
        for subj, grade, date in data:
            tree.insert('', 'end', values=(subj, grade, date))

        if subject != "Все":
            avg = get_avg_by_subject(current_user[0], subject)
            avg_label.config(text=f"Средний балл по «{subject}»: {round(avg, 2) if avg else 'нет данных'}")
        else:
            avg_label.config(text="")

    def show_avg():
        subject = subject_combobox.get()
        if subject == "Все":
            messagebox.showinfo("Средний балл", "Выберите конкретный предмет")
            return
        avg = get_avg_by_subject(current_user[0], subject)
        messagebox.showinfo("Средний балл", f"{subject}: {round(avg, 2) if avg else 'нет данных'}")

    refresh_table()

def display_teacher(win):
    win.title("Панель учителя")
    win.geometry("700x700")
    win.configure(bg="#f0f0f0")

    main_frame = tk.Frame(win, bg="#f0f0f0", padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    label_font = ("Helvetica", 12)
    entry_font = ("Helvetica", 11)

    tk.Label(main_frame, text="Выбор группы:", font=label_font, bg="#f0f0f0").grid(row=0, column=0, sticky="w", pady=5)
    group_var = tk.StringVar()
    group_combo = ttk.Combobox(main_frame, textvariable=group_var, state="readonly", width=30, font=entry_font)
    group_combo.grid(row=0, column=1, pady=5)

    tk.Label(main_frame, text="ФИО ученика:", font=label_font, bg="#f0f0f0").grid(row=1, column=0, sticky="w", pady=5)
    student_var = tk.StringVar()
    student_combo = ttk.Combobox(main_frame, textvariable=student_var, state="readonly", width=30, font=entry_font)
    student_combo.grid(row=1, column=1, pady=5)

    # === Предмет ===
    tk.Label(main_frame, text="Выбор предмета:", font=label_font, bg="#f0f0f0").grid(row=2, column=0, sticky="w", pady=5)
    subject_var = tk.StringVar()
    subject_combo = ttk.Combobox(main_frame, textvariable=subject_var, state="readonly", width=30, font=entry_font)
    subject_combo.grid(row=2, column=1, pady=5)

    def update_subjects():
        subjects = get_subjects()
        subject_combo['values'] = subjects
        subject_var.set(subjects[0] if subjects else "")

    update_subjects()

    tk.Label(main_frame, text="Новый предмет:", font=label_font, bg="#f0f0f0").grid(row=3, column=0, sticky="w", pady=5)
    entry_new_subject = tk.Entry(main_frame, font=entry_font, width=33)
    entry_new_subject.grid(row=3, column=1, pady=5)

    def add_new_subject():
        new_subj = entry_new_subject.get().strip()
        if not new_subj:
            messagebox.showwarning("Пусто", "Введите название предмета")
            return
        if new_subj in get_subjects():
            messagebox.showinfo("Инфо", "Такой предмет уже существует")
            return

        conn = sqlite3.connect("diary.db")
        conn.execute("INSERT INTO subjects (name) VALUES (?)", (new_subj,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Успех", f"Предмет '{new_subj}' добавлен")
        update_subjects()

    tk.Button(main_frame, text="Добавить предмет", command=add_new_subject,
              bg="#2196F3", fg="white", font=label_font, width=25).grid(row=4, column=0, columnspan=2, pady=10)

    tk.Label(main_frame, text="Оценка (1-5):", font=label_font, bg="#f0f0f0").grid(row=5, column=0, sticky="w", pady=5)
    entry_grade = tk.Entry(main_frame, font=entry_font, width=33)
    entry_grade.grid(row=5, column=1, pady=5)

    tk.Label(main_frame, text="Дата (дд-мм-гггг):", font=label_font, bg="#f0f0f0").grid(row=6, column=0, sticky="w", pady=5)
    entry_date = tk.Entry(main_frame, font=entry_font, width=33)
    entry_date.grid(row=6, column=1, pady=5)

    def is_valid_date(date_str):
        try:
            datetime.strptime(date_str, "%d-%m-%Y")
            return True
        except ValueError:
            return False

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

        date_str = entry_date.get().strip()
        if not is_valid_date(date_str):
            messagebox.showerror("Ошибка", "Введите корректную дату в формате дд-мм-гггг")
            return

        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE fio=? AND role='student'", (fio,))
        stu = c.fetchone()
        if not stu:
            messagebox.showerror("Ошибка", "Ученик не найден")
            conn.close()
            return

        c.execute("INSERT INTO grades (student_id, subject, grade, date) VALUES (?, ?, ?, ?)",
                  (stu[0], subject, grade, date_str))
        conn.commit()
        conn.close()
        messagebox.showinfo("Ок", "Оценка добавлена")

    def show_avg():
        subject = subject_combo.get()
        fio = student_combo.get()

        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE fio=? AND role='student'", (fio,))
        stu = c.fetchone()
        if not stu:
            messagebox.showwarning("Ошибка", "Студент не найден")
            conn.close()
            return

        c.execute("SELECT AVG(grade) FROM grades WHERE student_id=? AND subject=?", (stu[0], subject))
        avg = c.fetchone()[0]
        conn.close()

        messagebox.showinfo("Средний балл", f"{fio} по предмету {subject}: {round(avg, 2) if avg else 'нет данных'}")

    tk.Button(main_frame, text="Добавить оценку", command=submit_grade,
              bg="#4CAF50", fg="white", font=label_font, width=25).grid(row=7, column=0, columnspan=2, pady=10)

    tk.Button(main_frame, text="Средний балл", command=show_avg,
              bg="#009688", fg="white", font=label_font, width=25).grid(row=8, column=0, columnspan=2, pady=5)

    def update_groups():
        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT DISTINCT group_name FROM users WHERE role='student'")
        groups = [g[0] for g in c.fetchall()]
        conn.close()
        group_combo['values'] = groups
        if groups:
            group_combo.current(0)
            update_students_by_group()

    def update_students_by_group(*_):
        selected_group = group_combo.get()
        conn = sqlite3.connect("diary.db")
        c = conn.cursor()
        c.execute("SELECT fio FROM users WHERE role='student' AND group_name=?", (selected_group,))
        students = [s[0] for s in c.fetchall()]
        conn.close()
        student_combo['values'] = students
        if students:
            student_combo.current(0)

    group_combo.bind("<<ComboboxSelected>>", update_students_by_group)
    group_var.trace_add("write", update_students_by_group)

    student_combo.bind("<<ComboboxSelected>>", lambda _: None)

    update_groups()

login_frame = tk.Frame(root, bg="#f0f0f0", padx=30, pady=30)
login_frame.pack(expand=True)

tk.Label(login_frame, text="Вход в электронный дневник", font=("Helvetica", 16, "bold"), bg="#f0f0f0").grid(row=0, column=0, columnspan=2, pady=10)

tk.Label(login_frame, text="ФИО:", font=("Helvetica", 12), bg="#f0f0f0").grid(row=1, column=0, sticky="e", pady=5)
entry_login = tk.Entry(login_frame, width=30, font=("Helvetica", 12))
entry_login.grid(row=1, column=1, pady=5)

tk.Label(login_frame, text="Пароль:", font=("Helvetica", 12), bg="#f0f0f0").grid(row=2, column=0, sticky="e", pady=5)
entry_password = tk.Entry(login_frame, width=30, font=("Helvetica", 12), show="*")
entry_password.grid(row=2, column=1, pady=5)

tk.Button(login_frame, text="Войти", command=login, font=("Helvetica", 12), bg="#4CAF50", fg="white", width=20).grid(row=3, column=0, columnspan=2, pady=15)

init_db()

root.mainloop()