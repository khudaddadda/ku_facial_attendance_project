import customtkinter as ctk
from tkinter import ttk
import threading
import json
import os
from config import COLORS, IMAGES_PATH, NUM_FACE_SAMPLES
from utils import show_toast, generate_student_id, validate_email, validate_phone
from face_recognition_module import face_recognizer
from db import db




class StudentManagement(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.students = []
        self.face_embedding = None
        self.face_embeddings_list = None
        self.face_captured = False
        self.create_ui()
        self.load_students()

    def create_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color=COLORS['primary'], height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)
        ctk.CTkLabel(header_content, text="👥 Student Management", font=("Roboto", 24, "bold"), text_color="white").pack(side="left")
        add_btn = ctk.CTkButton(header_content, text="➕ Add New Student", font=("Roboto", 14, "bold"), fg_color=COLORS['success'], hover_color=COLORS['info'], height=40, corner_radius=8, command=self.show_add_student_form)
        add_btn.pack(side="right")

        # Main content
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Search frame
        search_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        search_frame.pack(fill="x", pady=(0, 15))
        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(search_inner, text="🔍 Search:", font=("Roboto", 13, "bold")).pack(side="left", padx=(0, 10))
        self.search_entry = ctk.CTkEntry(search_inner, width=250, height=35, placeholder_text="Search...", font=("Roboto", 13))
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_students())
        refresh_btn = ctk.CTkButton(search_inner, text="🔄 Refresh", width=100, height=35, font=("Roboto", 13, "bold"), fg_color=COLORS['info'], command=self.load_students)
        refresh_btn.pack(side="left")

        # Table
        table_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True)
        tree_container = ctk.CTkFrame(table_frame, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Student ID", "Name", "Roll No", "Department", "Year", "Email", "Phone")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="tree headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col, anchor="center")
        self.tree.column("#0", width=0)
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Student ID", width=120, anchor="center")
        self.tree.column("Name", width=180, anchor="w")
        self.tree.column("Roll No", width=100, anchor="center")
        self.tree.column("Department", width=150, anchor="center")
        self.tree.column("Year", width=80, anchor="center")
        self.tree.column("Email", width=200, anchor="w")
        self.tree.column("Phone", width=120, anchor="center")

        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Action buttons
        action_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=10)
        edit_btn = ctk.CTkButton(action_frame, text="✏️ Edit", width=120, height=35, font=("Roboto", 12, "bold"), fg_color=COLORS['warning'], command=self.edit_student)
        edit_btn.pack(side="left", padx=(0, 10))
        delete_btn = ctk.CTkButton(action_frame, text="🗑️ Delete", width=120, height=35, font=("Roboto", 12, "bold"), fg_color=COLORS['danger'], command=self.delete_student)
        delete_btn.pack(side="left")
        self.stats_label = ctk.CTkLabel(action_frame, text="Total: 0", font=("Roboto", 13, "bold"), text_color=COLORS['primary'])
        self.stats_label.pack(side="right")

    def load_students(self):
        self.students = db.get_all_students()
        self.display_students(self.students)

    def display_students(self, students):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, s in enumerate(students):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(s['id'], s['student_id'], s['name'], s['roll_no'], s['department'], s['year'], s['email'] or "N/A", s['phone'] or "N/A"), tags=(tag,))
        self.stats_label.configure(text=f"Total Students: {len(students)}")

    def search_students(self):
        term = self.search_entry.get().strip()
        if not term:
            self.load_students()
        else:
            results = db.search_students(term, 'name')
            self.display_students(results)

    def show_add_student_form(self):
        self.form_window = ctk.CTkToplevel(self)
        self.form_window.title("Add Student")
        self.form_window.geometry("550x750")
        self.form_window.resizable(False, False)
        self.form_window.grab_set()
        self.create_add_form()

    def create_add_form(self):
        self.face_captured = False
        self.face_embedding = None
        self.face_embeddings_list = None

        main_frame = ctk.CTkScrollableFrame(self.form_window, fg_color=COLORS['bg_light'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(main_frame, text="➕ Add New Student", font=("Roboto", 22, "bold"), text_color=COLORS['primary']).pack(pady=(0, 20))

        form_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=10)
        form_frame.pack(fill="x")
        form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_inner.pack(padx=30, pady=30)

        self.student_id_var = ctk.StringVar(value=generate_student_id())
        ctk.CTkLabel(form_inner, text="Student ID (Auto)", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(form_inner, width=450, height=35, textvariable=self.student_id_var, state="disabled").pack(pady=(0, 15))

        self.name_var = ctk.StringVar()
        ctk.CTkLabel(form_inner, text="Full Name *", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(form_inner, width=450, height=35, textvariable=self.name_var).pack(pady=(0, 15))

        self.roll_no_var = ctk.StringVar()
        ctk.CTkLabel(form_inner, text="Roll Number *", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(form_inner, width=450, height=35, textvariable=self.roll_no_var).pack(pady=(0, 15))

        self.department_var = ctk.StringVar(value="Computer Science")
        ctk.CTkLabel(form_inner, text="Department *", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkComboBox(form_inner, width=450, height=35, variable=self.department_var, values=["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil", "Electrical"]).pack(pady=(0, 15))

        self.year_var = ctk.StringVar(value="1st Year")
        ctk.CTkLabel(form_inner, text="Year *", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkComboBox(form_inner, width=450, height=35, variable=self.year_var, values=["1st Year", "2nd Year", "3rd Year", "4th Year"]).pack(pady=(0, 15))

        self.email_var = ctk.StringVar()
        ctk.CTkLabel(form_inner, text="Email", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(form_inner, width=450, height=35, textvariable=self.email_var).pack(pady=(0, 15))

        self.phone_var = ctk.StringVar()
        ctk.CTkLabel(form_inner, text="Phone", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(form_inner, width=450, height=35, textvariable=self.phone_var).pack(pady=(0, 15))

        self.capture_btn = ctk.CTkButton(form_inner, text="📸 Capture Face (3 samples)", width=450, height=40, font=("Roboto", 13, "bold"), fg_color=COLORS['info'], command=self.capture_student_faces_thread)
        self.capture_btn.pack(pady=(0, 10))
        self.capture_status = ctk.CTkLabel(form_inner, text="", font=("Roboto", 11))
        self.capture_status.pack(pady=(0, 15))

        btn_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(btn_frame, text="✅ Save", width=220, height=40, font=("Roboto", 14, "bold"), fg_color=COLORS['success'], command=self.save_student).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="❌ Cancel", width=220, height=40, font=("Roboto", 14, "bold"), fg_color=COLORS['danger'], command=self.form_window.destroy).pack(side="left")

    def capture_student_faces_thread(self):
        self.capture_btn.configure(state="disabled", text="Opening camera...")
        threading.Thread(target=self.capture_student_faces, daemon=True).start()

    def capture_student_faces(self):
        try:
            avg_emb, all_embs = face_recognizer.capture_multiple_faces(num_samples=NUM_FACE_SAMPLES)

            if avg_emb is not None and all_embs:
                self.face_embedding = avg_emb
                self.face_embeddings_list = all_embs
                self.face_captured = True
                self.form_window.after(
                    0,
                    self.update_capture_status,
                    True,
                    f"{len(all_embs)} face samples captured successfully!"
                )
            else:
                self.form_window.after(
                    0,
                    self.update_capture_status,
                    False,
                    "Face capture cancelled or no face detected"
                )

        except Exception as e:
            print("capture_student_faces error:", e)
            self.form_window.after(
                0,
                self.update_capture_status,
                False,
                f"Error: {e}"
            )

    def update_capture_status(self, success, msg):
        if success:
            self.capture_btn.configure(text="✅ Face Captured", fg_color=COLORS['success'], state="disabled")
            self.capture_status.configure(text=msg, text_color=COLORS['success'])
        else:
            self.capture_btn.configure(text="📸 Capture Face", state="normal")
            self.capture_status.configure(text=f"Error: {msg}", text_color=COLORS['danger'])

    def save_student(self):
        name = self.name_var.get().strip()
        roll_no = self.roll_no_var.get().strip()
        department = self.department_var.get().strip()
        year = self.year_var.get().strip()
        email = self.email_var.get().strip()
        phone = self.phone_var.get().strip()
        student_id = self.student_id_var.get()

        if not name or not roll_no or not department or not year:
            show_toast(self.form_window, "Please fill all required fields", "error")
            return
        if email and not validate_email(email):
            show_toast(self.form_window, "Invalid email", "error")
            return
        if phone and not validate_phone(phone):
            show_toast(self.form_window, "Phone must be 10 digits", "error")
            return
        if not self.face_captured:
            show_toast(self.form_window, "Please capture face first", "error")
            return

        dup = db.check_duplicate_face_student(self.face_embedding)
        if dup:
            show_toast(self.form_window, f"Face already registered to {dup['name']}", "error")
            return

        photo_path = f"{IMAGES_PATH}{student_id}.jpg"
        success = db.add_student(student_id, name, roll_no, department, year, email, phone, photo_path, self.face_embedding)
        if success:
            if self.face_embeddings_list and len(self.face_embeddings_list) > 1:
                db.add_multiple_face_embeddings(student_id, self.face_embeddings_list)
            show_toast(self.form_window, f"Student {name} added! ", "success")
            self.form_window.after(2000, self.form_window.destroy)
            self.load_students()
        else:
            show_toast(self.form_window, "Student ID or Roll No already exists", "error")

    def edit_student(self):
        selected = self.tree.selection()
        if not selected:
            show_toast(self, "Select a student to edit", "warning")
            return
        values = self.tree.item(selected[0])['values']
        student_id_db = values[0]

        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit Student")
        edit_window.geometry("500x650")
        edit_window.resizable(False, False)
        edit_window.grab_set()

        main_frame = ctk.CTkScrollableFrame(edit_window, fg_color=COLORS['bg_light'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(main_frame, text="✏️ Edit Student", font=("Roboto", 22, "bold"), text_color=COLORS['primary']).pack(pady=(0, 20))

        form_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=10)
        form_frame.pack(fill="x")
        form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_inner.pack(padx=30, pady=30)

        name_var = ctk.StringVar(value=values[2])
        roll_var = ctk.StringVar(value=values[3])
        dept_var = ctk.StringVar(value=values[4])
        year_var = ctk.StringVar(value=values[5])
        email_var = ctk.StringVar(value=values[6] if values[6] != "N/A" else "")
        phone_var = ctk.StringVar(value=values[7] if values[7] != "N/A" else "")

        for label, var in [("Full Name *", name_var), ("Roll Number *", roll_var)]:
            ctk.CTkLabel(form_inner, text=label, font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
            ctk.CTkEntry(form_inner, width=420, height=35, textvariable=var).pack(pady=(0, 15))

        ctk.CTkLabel(form_inner, text="Department *", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkComboBox(form_inner, width=420, height=35, variable=dept_var, values=["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil", "Electrical"]).pack(pady=(0, 15))

        ctk.CTkLabel(form_inner, text="Year *", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkComboBox(form_inner, width=420, height=35, variable=year_var, values=["1st Year", "2nd Year", "3rd Year", "4th Year"]).pack(pady=(0, 15))

        ctk.CTkLabel(form_inner, text="Email", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(form_inner, width=420, height=35, textvariable=email_var).pack(pady=(0, 15))

        ctk.CTkLabel(form_inner, text="Phone", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(form_inner, width=420, height=35, textvariable=phone_var).pack(pady=(0, 15))

        def update():
            if not name_var.get() or not roll_var.get():
                show_toast(edit_window, "Name and Roll No required", "error")
                return
            if email_var.get() and not validate_email(email_var.get()):
                show_toast(edit_window, "Invalid email", "error")
                return
            if phone_var.get() and not validate_phone(phone_var.get()):
                show_toast(edit_window, "Phone must be 10 digits", "error")
                return
            success = db.update_student(student_id_db, name_var.get(), roll_var.get(), dept_var.get(), year_var.get(), email_var.get(), phone_var.get())
            if success:
                show_toast(edit_window, "Updated! ", "success")
                edit_window.after(1500, edit_window.destroy)
                self.load_students()
            else:
                show_toast(edit_window, "Update failed", "error")

        btn_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        ctk.CTkButton(btn_frame, text="✅ Update", width=200, height=40, font=("Roboto", 14, "bold"), fg_color=COLORS['success'], command=update).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="❌ Cancel", width=200, height=40, font=("Roboto", 14, "bold"), fg_color=COLORS['danger'], command=edit_window.destroy).pack(side="left")

    def delete_student(self):
        selected = self.tree.selection()
        if not selected:
            show_toast(self, "Select a student to delete", "warning")
            return
        values = self.tree.item(selected[0])['values']
        student_id_db = values[0]
        name = values[2]

        confirm = ctk.CTkToplevel(self)
        confirm.title("Confirm Delete")
        confirm.geometry("400x200")
        confirm.resizable(False, False)
        confirm.grab_set()
        confirm.transient(self)

        frame = ctk.CTkFrame(confirm, fg_color=COLORS['bg_light'])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame, text="⚠️ Confirm Delete", font=("Roboto", 18, "bold"), text_color=COLORS['danger']).pack(pady=(0, 15))
        ctk.CTkLabel(frame, text=f"Delete {name}?", font=("Roboto", 14)).pack()

        def do_delete():
            if db.delete_student(student_id_db):
                show_toast(self, f"{name} deleted", "success")
                confirm.destroy()
                self.load_students()
            else:
                show_toast(confirm, "Delete failed", "error")

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=(20, 0))
        ctk.CTkButton(btn_frame, text="Yes", width=120, height=35, fg_color=COLORS['danger'], command=do_delete).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="No", width=120, height=35, fg_color="gray", command=confirm.destroy).pack(side="left")