import customtkinter as ctk
from datetime import datetime
import threading
import json
from config import COLORS, APP_TITLE
from utils import show_toast, get_display_date, get_display_time
from student import StudentManagement
from attendance import AttendanceModule
from face_recognition_module import face_recognizer
from db import db



class Dashboard(ctk.CTkFrame):
    """Main dashboard interface"""

    def __init__(self, parent, user_data, on_logout):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.user_data = user_data
        self.on_logout = on_logout
        self.current_frame = None

        self.create_ui()
        self.show_home()
        self.update_clock()

    def create_ui(self):
        """Create dashboard UI"""
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, fg_color=COLORS['dark'], width=250, corner_radius=0)
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
            text="Attendance System",
            font=("Roboto", 14, "bold"),
            text_color="white"
        ).pack(pady=(0, 10))

        # User info
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.pack(fill="x", padx=15, pady=(0, 30))

        ctk.CTkLabel(
            user_frame,
            text=f"Welcome,",
            font=("Roboto", 11),
            text_color="gray"
        ).pack(anchor="w")

        ctk.CTkLabel(
            user_frame,
            text=self.user_data['name'],
            font=("Roboto", 15, "bold"),
            text_color="white"
        ).pack(anchor="w")

        # Navigation buttons
        nav_buttons = [
            ("🏠 Dashboard", self.show_home, COLORS['primary']),
            ("👥 Student Management", self.show_students, COLORS['secondary']),
            ("📸 Mark Attendance", self.start_face_recognition, COLORS['success']),
            ("📊 Attendance Report", self.show_attendance, COLORS['info']),
        ]

        for text, command, color in nav_buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                font=("Roboto", 14, "bold"),
                fg_color=color,
                hover_color=COLORS['secondary'],
                height=50,
                anchor="w",
                corner_radius=8,
                command=command
            )
            btn.pack(fill="x", padx=15, pady=5)

        # Logout button (at bottom)
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
        logout_btn.pack(side="bottom", fill="x", padx=15, pady=15)

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