import customtkinter as ctk
from datetime import datetime
import threading
import json
from config import COLORS, APP_TITLE
from utils import show_toast, get_display_date, get_display_time
from student import StudentManagement
from attendance import AttendanceModule
from face_recognition_module import face_recognizer
from palm_recognition_module import palm_recognizer
from iris_recognition_module import IrisRecognizer
from db import db
from fingerprint_module import fingerprint_module
from fingerprint_module import fingerprint_module
#=========createing object========
#palm_recognizer = PalmRecognizer()
iris_recognizer = IrisRecognizer()



class Dashboard(ctk.CTkFrame):
    """Main dashboard interface"""

    def __init__(self, parent, user_data, on_logout):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.user_data = user_data
        self.user_role = user_data.get("role", "admin")
        self.on_logout = on_logout
        self.current_frame = None

        self.create_ui()
        self.show_home()
        self.update_clock()

    def create_ui(self):
        """Create dashboard UI"""
        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=COLORS['dark'],
            width=250,
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo/Title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color=COLORS['primary'], height=100)
        logo_frame.pack(fill="x", padx=10, pady=(10, 20))

        ctk.CTkLabel(
            logo_frame,
            text="🎓",
            font=("Roboto", 40)
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            logo_frame,
            #text="Attendance System",
            text="facial recognition Attendance System",
            font=("Roboto", 14, "bold"),
            text_color="white"
        ).pack(pady=(0, 10))

        # User info
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.pack(fill="x", padx=15, pady=(0, 30))

        ctk.CTkLabel(
            user_frame,
            text="Welcome,",
            font=("Roboto", 11),
            text_color="gray"
        ).pack(anchor="w")

        ctk.CTkLabel(
            user_frame,
            text=self.user_data['name'],
            font=("Roboto", 15, "bold"),
            text_color="white"
        ).pack(anchor="w")

        role_text = "Super Admin" if self.user_role == "super_admin" else "Admin"

        ctk.CTkLabel(
            user_frame,
            text=f"Role: {role_text}",
            font=("Roboto", 12, "bold"),
            text_color="#fbbf24" if self.user_role == "super_admin" else "#93c5fd"
        ).pack(anchor="w", pady=(4, 0))

        # Navigation buttons plus tested button
        nav_buttons = [
            ("🏠 Dashboard", self.show_home, COLORS['primary']),
            ("👥 Student Management", self.show_students, COLORS['secondary']),
            ("📸 Mark Attendance", self.open_attendance_menu, COLORS['success']),
            ("🖐 Test Palm", self.start_palm_test, "#f59e0b"),
            ("👁 Test Iris", self.start_iris_test, "#8b5cf6"),
            ("📊 Attendance Report", self.show_attendance, COLORS['info']),
        ]

        if self.user_role == "super_admin":
            nav_buttons.extend([
                ("🛡️ Manage Admins", self.show_manage_admins, "#7c3aed"),
                ("⚙️ System Overview", self.show_system_overview, "#ea580c"),
            ])
            
        # Scrollable menu area
        self.menu_scroll = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            width=220
        )
        self.menu_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        for text, command, color in nav_buttons:
            btn = ctk.CTkButton(
                self.menu_scroll,
                text=text,
                font=("Roboto", 14, "bold"),
                fg_color=color,
                hover_color=COLORS['secondary'],
                height=50,
                anchor="w",
                corner_radius=8,
                command=command
            )
            btn.pack(fill="x", padx=10, pady=5)

        # Logout button
        logout_btn = ctk.CTkButton(
            self.sidebar,
            text="🚪 Logout",
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            height=45,
            corner_radius=8,
            command=self.logout
        )
        logout_btn.pack(fill="x", padx=15, pady=15)

        # Main content area
        self.content_area = ctk.CTkFrame(self, fg_color=COLORS['bg_light'])
        self.content_area.pack(side="right", fill="both", expand=True)

    def clear_content(self):
        """Clear current content"""
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

    def show_home(self):
        """Show home/dashboard"""
        self.clear_content()
        self.current_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True)

        # Header
        header = ctk.CTkFrame(self.current_frame, fg_color=COLORS['primary'], height=120, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=25)

        # Title and date
        left_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        left_frame.pack(side="left", fill="y")

        ctk.CTkLabel(
            left_frame,
            text="Dashboard",
            font=("Roboto", 28, "bold"),
            text_color="white"
        ).pack(anchor="w")

        self.date_label = ctk.CTkLabel(
            left_frame,
            text=get_display_date(),
            font=("Roboto", 14),
            text_color="white"
        )
        self.date_label.pack(anchor="w", pady=(5, 0))

        # Clock
        self.clock_label = ctk.CTkLabel(
            header_content,
            text=get_display_time(),
            font=("Roboto", 32, "bold"),
            text_color="white"
        )
        self.clock_label.pack(side="right")

        # Stats cards
        stats_container = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        stats_container.pack(fill="x", padx=30, pady=30)

        # Get stats
        stats = db.get_attendance_stats()

        # Stats data
        stats_data = [
            ("👥 Total Students", stats['total_students'], COLORS['primary']),
            ("✅ Present Today", stats['present_today'], COLORS['success']),
            ("❌ Absent Today", stats['absent_today'], COLORS['danger'])
        ]

        for title, value, color in stats_data:
            card = ctk.CTkFrame(
                stats_container,
                fg_color="white",
                corner_radius=15,
                border_width=2,
                border_color=color
            )
            card.pack(side="left", fill="both", expand=True, padx=10)

            card_content = ctk.CTkFrame(card, fg_color="transparent")
            card_content.pack(padx=30, pady=30)

            ctk.CTkLabel(
                card_content,
                text=title,
                font=("Roboto", 16, "bold"),
                text_color="gray"
            ).pack()

            ctk.CTkLabel(
                card_content,
                text=str(value),
                font=("Roboto", 48, "bold"),
                text_color=color
            ).pack(pady=(10, 0))

        # Graph frame
        graph_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        graph_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        ctk.CTkLabel(
            graph_frame,
            text="📊 Attendance Trend (Last 7 Days)",
            font=("Roboto", 20, "bold"),
            text_color=COLORS['dark']
        ).pack(anchor="w", pady=(0, 20))

        # Create graph
        self.create_attendance_graph(graph_frame)
        
    def show_manage_admins(self):
        """Show super admin admin-management page"""
        self.clear_content()

        self.current_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.current_frame,
            text="🛡️ Manage Admins",
            font=("Roboto", 24, "bold"),
            text_color=COLORS['dark']
        ).pack(anchor="w", pady=(0, 20))

        # Top action bar
        top_bar = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(
            top_bar,
            text="➕ Add New Admin",
            font=("Roboto", 13, "bold"),
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self.open_create_admin
        ).pack(side="left")

        # Table area
        table_frame = ctk.CTkFrame(
            self.current_frame,
            fg_color="white",
            corner_radius=15,
            border_width=2,
            border_color="#7c3aed"
        )
        table_frame.pack(fill="both", expand=True)

        admins = db.get_admin_users()

        if not admins:
            ctk.CTkLabel(
                table_frame,
                text="No admin accounts found",
                font=("Roboto", 14),
                text_color="gray"
            ).pack(pady=40)
            return

        for admin in admins:
            row = ctk.CTkFrame(table_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=10)

            info_text = f"{admin['name']}  |  {admin['username']}  |  {admin['role']}"
            ctk.CTkLabel(
                row,
                text=info_text,
                font=("Roboto", 13),
                text_color=COLORS['dark']
            ).pack(side="left")

            if admin["id"] != self.user_data["id"]:
                ctk.CTkButton(
                    row,
                    text="Delete",
                    width=90,
                    fg_color=COLORS['danger'],
                    hover_color="#dc2626",
                    command=lambda admin_id=admin["id"]: self.delete_admin(admin_id)
                ).pack(side="right")
                
                
    # attandance menu
    def open_attendance_menu(self):
        """Open menu for selecting attendance method"""
        import customtkinter as ctk

        menu = ctk.CTkToplevel(self)
        menu.title("Select Attendance Method")
        menu.geometry("400x300")
        menu.grab_set()

        frame = ctk.CTkFrame(menu)
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(frame, text="Choose Method", font=("Roboto", 18, "bold")).pack(pady=10)

        # Face button
        ctk.CTkButton(
            frame,
            text="📸 Face Recognition",
            command=lambda: [menu.destroy(), self.start_face_recognition()]
        ).pack(fill="x", pady=5)

        # Fingerprint button
        ctk.CTkButton(
            frame,
            text="🔑 Fingerprint",
            command=lambda: [menu.destroy(), self.start_fingerprint_attendance()]
        ).pack(fill="x", pady=5)

        # Palm (test only)
        ctk.CTkButton(
            frame,
            text="🖐 Palm (Test Only)",
            command=lambda: [menu.destroy(), self.start_palm_test()]
        ).pack(fill="x", pady=5)

        # Iris (test only)
        ctk.CTkButton(
            frame,
            text="👁 Iris (Test Only)",
            command=lambda: [menu.destroy(), self.start_iris_test()]
        ).pack(fill="x", pady=5)
        
    # fingerprint atttandance
    def start_fingerprint_attendance(self):
        """Start continuous fingerprint attendance in background"""
        if hasattr(self, "fingerprint_running") and self.fingerprint_running:
            show_toast(self, "Fingerprint attendance already running", "warning")
            return

        self.fingerprint_running = True
        threading.Thread(target=self.run_fingerprint_attendance, daemon=True).start()
        
        
        
    def run_fingerprint_attendance(self):
        """Continuously scan fingerprints and mark attendance"""

        self.after(0, lambda: show_toast(self, "Fingerprint attendance started", "info"))

        while self.fingerprint_running:
            try:
                fingerprint_id = fingerprint_module.read_fingerprint_id()

                if fingerprint_id is None:
                    continue

                students = db.get_all_students()
                matched_student = None

                for student in students:
                    if student.get("fingerprint_id") == fingerprint_id:
                        matched_student = student
                        break

                if not matched_student:
                    self.after(
                        0,
                        lambda fid=fingerprint_id: show_toast(
                            self,
                            f"No student linked to fingerprint ID {fid}",
                            "error"
                        )
                    )
                    continue

                success, msg = db.mark_attendance(
                    matched_student["student_id"],
                    matched_student["name"],
                    matched_student["department"],
                    datetime.now().date(),
                    datetime.now().time()
                )

                if success:
                    self.after(
                        0,
                        lambda name=matched_student["name"]: show_toast(
                            self,
                            f"Attendance marked for {name}",
                            "success"
                        )
                    )

                    # Refresh attendance report if it is currently open
                    if hasattr(self.current_frame, "load_attendance"):
                        self.after(0, self.current_frame.load_attendance)

                    # Refresh dashboard stats if needed
                    self.after(1000, self.show_home)
                else:
                    self.after(
                        0,
                        lambda message=msg: show_toast(self, message, "warning")
                    )

            except Exception as e:
                self.after(
                    0,
                    lambda err=str(e): show_toast(
                        self,
                        f"Fingerprint error: {err}",
                        "error"
                    )
                )
                self.fingerprint_running = False

    def create_attendance_graph(self, parent):
        """Create attendance trend graph using matplotlib"""
        import customtkinter as ctk
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
        import matplotlib.dates as mdates

        trend_data = db.get_attendance_trend(days=7)

        if not trend_data:
            ctk.CTkLabel(
                parent,
                text="No attendance data available",
                font=("Roboto", 14),
                text_color="gray"
            ).pack(pady=50)
            return

        dates = [item['date'] for item in trend_data]
        counts = [item['count'] for item in trend_data]
        percentages = [item['percentage'] for item in trend_data]

        outer_frame = ctk.CTkFrame(
            parent,
            fg_color="white",
            corner_radius=15,
            border_width=2,
            border_color=COLORS['primary']
        )
        outer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        title_label = ctk.CTkLabel(
            outer_frame,
            text="Daily Attendance Tracking",
            font=("Roboto", 18, "bold"),
            text_color="#1f2937"
        )
        title_label.pack(pady=(15, 5))

        chart_frame = ctk.CTkFrame(outer_frame, fg_color="white")
        chart_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        fig = Figure(figsize=(12, 4.8), dpi=100, facecolor="white")
        ax = fig.add_subplot(111)

        ax.plot(
            dates,
            counts,
            marker='o',
            markersize=8,
            linewidth=3,
            color='#22C55E',
            markerfacecolor='#22C55E',
            markeredgecolor='white',
            markeredgewidth=2
        )

        ax.fill_between(dates, counts, alpha=0.2, color='#22C55E')

        for date, count, pct in zip(dates, counts, percentages):
            ax.annotate(
                f'{count}\n({pct}%)',
                xy=(date, count),
                xytext=(0, 12),
                textcoords='offset points',
                ha='center',
                fontsize=9,
                fontweight='bold',
                color='#1f2937'
            )

        ax.set_xlabel('Date', fontsize=12, fontweight='bold', color='#4b5563', labelpad=12)
        ax.set_ylabel('Students Present', fontsize=12, fontweight='bold', color='#4b5563')

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.tick_params(axis='x', labelrotation=30, labelsize=10, colors='#4b5563')
        ax.tick_params(axis='y', labelsize=10, colors='#4b5563')

        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
        ax.set_axisbelow(True)
        ax.set_ylim(bottom=0)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#d1d5db')
        ax.spines['bottom'].set_color('#d1d5db')

        # Extra bottom space so month labels like "Apr" are fully visible
        fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.22)

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def update_clock(self):
        """Update clock every second"""
        try:
            if hasattr(self, 'clock_label') and self.clock_label.winfo_exists():
                self.clock_label.configure(text=get_display_time())
            if hasattr(self, 'date_label') and self.date_label.winfo_exists():
                self.date_label.configure(text=get_display_date())
            self.after(1000, self.update_clock)
        except:
            pass

    def show_students(self):
        """Show student management"""
        self.clear_content()
        self.current_frame = StudentManagement(self.content_area)
        self.current_frame.pack(fill="both", expand=True)

    def show_attendance(self):
        """Show attendance records"""
        self.clear_content()
        self.current_frame = AttendanceModule(self.content_area)
        self.current_frame.pack(fill="both", expand=True)

    def start_face_recognition(self):
        """Start face recognition for attendance marking"""
        # Confirmation
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Mark Attendance")
        confirm_window.geometry("450x200")
        confirm_window.resizable(False, False)
        confirm_window.grab_set()
        confirm_window.transient(self)

        # Center window
        confirm_window.update_idletasks()
        width = confirm_window.winfo_width()
        height = confirm_window.winfo_height()
        x = (confirm_window.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (height // 2)
        confirm_window.geometry(f"{width}x{height}+{x}+{y}")

        frame = ctk.CTkFrame(confirm_window, fg_color=COLORS['bg_light'])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="📸 Start Face Recognition?",
            font=("Roboto", 20, "bold"),
            text_color=COLORS['primary']
        ).pack(pady=(10, 15))

        ctk.CTkLabel(
            frame,
            text="Camera will open for real-time attendance marking.\nPress ESC to stop.",
            font=("Roboto", 13),
            text_color="gray",
            wraplength=400
        ).pack(pady=(0, 20))

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        def start_recognition():
            confirm_window.destroy()
            threading.Thread(target=self.run_face_recognition, daemon=True).start()

        ctk.CTkButton(
            button_frame,
            text="✅ Start",
            width=150,
            height=40,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['info'],
            command=start_recognition
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            width=150,
            height=40,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            command=confirm_window.destroy
        ).pack(side="left")

    def run_face_recognition(self):
        """Run face recognition for attendance"""
        try:
            # Get all students with embeddings (advanced version for high accuracy)
            database_students = db.get_all_student_embeddings_advanced()

            if not database_students:
                self.after(0, lambda: show_toast(self, "No students registered", "warning"))
                return

            # Callback for marking attendance
            def mark_attendance_callback(student_id):
                student_data = database_students.get(student_id, {})
                if student_data:
                    success, message = db.mark_attendance(
                        student_id,
                        student_data['name'],
                        student_data['department'],
                        datetime.now().date(),
                        datetime.now().time()
                    )
                    if success:
                        self.after(0, lambda: show_toast(self, f" Attendance marked for {student_data['name']}", "success"))
                        return True
                    else:
                        self.after(0, lambda: show_toast(self, message, "warning"))
                        return False
                return False

            # Start detection
            marked_count = face_recognizer.detect_and_mark_attendance(database_students, mark_attendance_callback)

            # Show completion message
            self.after(0, lambda: show_toast(self, f"Attendance marking completed. Total: {marked_count}", "info"))

            # Refresh if on home
            if hasattr(self.current_frame, 'stats_label'):
                self.after(1000, self.show_home)

        except Exception as e:
            self.after(0, lambda: show_toast(self, f"Recognition error: {str(e)}", "error"))
            
            
    #===============tested palm method
    
    def start_palm_test(self):
        """Open confirmation and start palm recognition in test mode"""
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Test Palm Recognition")
        confirm_window.geometry("450x200")
        confirm_window.resizable(False, False)
        confirm_window.grab_set()
        confirm_window.transient(self)

        confirm_window.update_idletasks()
        width = confirm_window.winfo_width()
        height = confirm_window.winfo_height()
        x = (confirm_window.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (height // 2)
        confirm_window.geometry(f"{width}x{height}+{x}+{y}")

        frame = ctk.CTkFrame(confirm_window, fg_color=COLORS['bg_light'])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="🖐 Start Palm Test?",
            font=("Roboto", 20, "bold"),
            text_color="#f59e0b"
        ).pack(pady=(10, 15))

        ctk.CTkLabel(
            frame,
            text="Camera will open for palm recognition test only.\nAttendance will NOT be marked.",
            font=("Roboto", 13),
            text_color="gray",
            wraplength=400
        ).pack(pady=(0, 20))

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        def start_test():
            confirm_window.destroy()
            threading.Thread(target=self.run_palm_test, daemon=True).start()

        ctk.CTkButton(
            button_frame,
            text="✅ Start",
            width=150,
            height=40,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['info'],
            command=start_test
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            width=150,
            height=40,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            command=confirm_window.destroy
        ).pack(side="left")


    def run_palm_test(self):
        """Run palm recognition in test mode only"""
        try:
            students = db.get_all_students()

            stored_embeddings = []
            for student in students:
                palm_embedding = student.get("palm_embedding")
                if palm_embedding:
                    try:
                        if isinstance(palm_embedding, str):
                            palm_embedding = json.loads(palm_embedding)

                        stored_embeddings.append({
                            "id": student["student_id"],
                            "name": student["name"],
                            "embedding": palm_embedding
                        })
                    except Exception as e:
                        print("Palm embedding parse error:", e)

            if not stored_embeddings:
                self.after(0, lambda: show_toast(self, "No palm data found", "warning"))
                return

            match = palm_recognizer.recognize_palm(stored_embeddings)

            if match:
                name = match.get("name", "Unknown")
                self.after(0, lambda: show_toast(self, f"Palm matched: {name}", "success"))
            else:
                self.after(0, lambda: show_toast(self, "No palm match found", "warning"))

        except Exception as e:
            error_message = str(e)
            self.after(0, lambda msg=error_message: show_toast(self, f"Palm test error: {msg}", "error")) 
            
            
            
            
    #=========iris test method=====
    
    def start_iris_test(self):
        """Open confirmation and start iris recognition in test mode"""
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Test Iris Recognition")
        confirm_window.geometry("450x200")
        confirm_window.resizable(False, False)
        confirm_window.grab_set()
        confirm_window.transient(self)

        confirm_window.update_idletasks()
        width = confirm_window.winfo_width()
        height = confirm_window.winfo_height()
        x = (confirm_window.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (height // 2)
        confirm_window.geometry(f"{width}x{height}+{x}+{y}")

        frame = ctk.CTkFrame(confirm_window, fg_color=COLORS['bg_light'])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="👁 Start Iris Test?",
            font=("Roboto", 20, "bold"),
            text_color="#8b5cf6"
        ).pack(pady=(10, 15))

        ctk.CTkLabel(
            frame,
            text="Camera will open for iris recognition test only.\nAttendance will NOT be marked.",
            font=("Roboto", 13),
            text_color="gray",
            wraplength=400
        ).pack(pady=(0, 20))

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        def start_test():
            confirm_window.destroy()
            threading.Thread(target=self.run_iris_test, daemon=True).start()

        ctk.CTkButton(
            button_frame,
            text="✅ Start",
            width=150,
            height=40,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['info'],
            command=start_test
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            width=150,
            height=40,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            command=confirm_window.destroy
        ).pack(side="left")


    def run_iris_test(self):
        """Run iris recognition in test mode only"""
        try:
            students = db.get_all_students()

            stored_embeddings = []
            for student in students:
                iris_embedding = student.get("iris_embedding")
                if iris_embedding:
                    try:
                        if isinstance(iris_embedding, str):
                            iris_embedding = json.loads(iris_embedding)

                        stored_embeddings.append({
                            "id": student["student_id"],
                            "name": student["name"],
                            "embedding": iris_embedding
                        })
                    except Exception as e:
                        print("Iris embedding parse error:", e)

            if not stored_embeddings:
                self.after(0, lambda: show_toast(self, "No iris data found", "warning"))
                return

            match = iris_recognizer.recognize_iris(stored_embeddings)

            if match:
                name = match.get("name", "Unknown")
                self.after(0, lambda: show_toast(self, f"Iris matched: {name}", "success"))
            else:
                self.after(0, lambda: show_toast(self, "No iris match found", "warning"))

        except Exception as e:
            error_message = str(e)
            self.after(0, lambda msg=error_message: show_toast(self, f"Iris test error: {msg}", "error"))
    
    
    
    
    #delete admin      
    def delete_admin(self, admin_id):
        """Delete an admin account"""
        if self.user_role != "super_admin":
            show_toast(self, "Access denied", "error")
            return

        success = db.delete_user_by_id(admin_id)

        if success:
            show_toast(self, "Admin deleted successfully", "success")
            self.show_manage_admins()
        else:
            show_toast(self, "Failed to delete admin", "error")
    def open_create_admin(self):
        """Open register page for super admin to create another admin"""
        if self.user_role != "super_admin":
            show_toast(self, "Access denied", "error")
            return

        self.parent.show_register(return_to_dashboard=True)
        
        
    def show_system_overview(self):
        """Show super admin system overview"""
        self.clear_content()

        self.current_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.current_frame,
            text="⚙️ System Overview",
            font=("Roboto", 24, "bold"),
            text_color=COLORS['dark']
        ).pack(anchor="w", pady=(0, 20))

        stats = db.get_attendance_stats()
        users = db.get_admin_users()

        cards = [
            ("👥 Total Students", stats["total_students"], COLORS["primary"]),
            ("✅ Present Today", stats["present_today"], COLORS["success"]),
            ("❌ Absent Today", stats["absent_today"], COLORS["danger"]),
            ("🛡️ Total Admins", len(users), "#7c3aed"),
        ]

        cards_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        cards_frame.pack(fill="x")

        for title, value, color in cards:
            card = ctk.CTkFrame(
                cards_frame,
                fg_color="white",
                corner_radius=15,
                border_width=2,
                border_color=color
            )
            card.pack(side="left", fill="both", expand=True, padx=10)

            ctk.CTkLabel(
                card,
                text=title,
                font=("Roboto", 15, "bold"),
                text_color="gray"
            ).pack(pady=(20, 8))

            ctk.CTkLabel(
                card,
                text=str(value),
                font=("Roboto", 34, "bold"),
                text_color=color
            ).pack(pady=(0, 20))

    def logout(self):
        """Logout user"""
        # Confirmation
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Logout")
        confirm_window.geometry("350x170")
        confirm_window.resizable(False, False)
        confirm_window.grab_set()
        confirm_window.transient(self)

        # Center window
        confirm_window.update_idletasks()
        width = confirm_window.winfo_width()
        height = confirm_window.winfo_height()
        x = (confirm_window.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (height // 2)
        confirm_window.geometry(f"{width}x{height}+{x}+{y}")

        frame = ctk.CTkFrame(confirm_window, fg_color=COLORS['bg_light'])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="🚪 Logout",
            font=("Roboto", 18, "bold"),
            text_color=COLORS['danger']
        ).pack(pady=(5, 10))

        ctk.CTkLabel(
            frame,
            text="Are you sure you want to logout?",
            font=("Roboto", 12)
        ).pack(pady=(0, 20))

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        ctk.CTkButton(
            button_frame,
            text="✅ Yes",
            width=120,
            height=35,
            font=("Roboto", 12, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            command=lambda: (confirm_window.destroy(), self.on_logout())
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="❌ No",
            width=120,
            height=35,
            font=("Roboto", 12, "bold"),
            fg_color="gray",
            hover_color="#6b7280",
            command=confirm_window.destroy
        ).pack(side="left")