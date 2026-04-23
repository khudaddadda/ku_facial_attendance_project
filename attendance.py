import customtkinter as ctk
from tkinter import ttk
import threading
from config import COLORS
from utils import show_toast, format_date, format_time, get_current_date, export_to_excel, LoadingDialog
from db import db
from datetime import datetime, timedelta
from tkcalendar import DateEntry




class AttendanceModule(ctk.CTkFrame):
    """Attendance viewing and management interface"""

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.attendance_records = []
        self.create_ui()
        self.load_attendance()

    def create_ui(self):
        """Create attendance UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color=COLORS['primary'], height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            header_content,
            text="📊 Attendance Records",
            font=("Roboto", 24, "bold"),
            text_color="white"
        ).pack(side="left")

        # Export button
        export_btn = ctk.CTkButton(
            header_content,
            text="📂 Export to Excel",
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['info'],
            height=40,
            corner_radius=8,
            command=self.export_to_excel_thread
        )
        export_btn.pack(side="right")

        # Main content
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Filter frame
        filter_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 15))

        filter_inner = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_inner.pack(fill="x", padx=20, pady=15)

        # Date filter label
        ctk.CTkLabel(filter_inner, text="📅 Date:", font=("Roboto", 13, "bold")).pack(side="left", padx=(0, 10))

        # Date picker
        self.date_picker = DateEntry(
            filter_inner,
            width=15,
            background=COLORS['primary'],
            foreground='white',
            borderwidth=2,
            font=("Roboto", 14),
            date_pattern='yyyy-mm-dd',
            state='readonly'
        )
        self.date_picker.pack(side="left", padx=(0, 10))
        self.date_picker.bind("<<DateEntrySelected>>", lambda e: self.apply_filters())

        # Quick date buttons
        today_btn = ctk.CTkButton(
            filter_inner,
            text="Today",
            width=80,
            height=35,
            font=("Roboto", 12, "bold"),
            fg_color=COLORS['info'],
            hover_color=COLORS['secondary'],
            command=self.set_today
        )
        today_btn.pack(side="left", padx=(0, 5))

        yesterday_btn = ctk.CTkButton(
            filter_inner,
            text="Yesterday",
            width=90,
            height=35,
            font=("Roboto", 12, "bold"),
            fg_color=COLORS['info'],
            hover_color=COLORS['secondary'],
            command=self.set_yesterday
        )
        yesterday_btn.pack(side="left", padx=(0, 15))

        # Department filter
        ctk.CTkLabel(filter_inner, text="🏢 Department:", font=("Roboto", 13, "bold")).pack(side="left", padx=(0, 10))

        self.dept_filter = ctk.CTkComboBox(
            filter_inner,
            width=180,
            height=35,
            values=["All", "Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil", "Electrical"],
            font=("Roboto", 12)
        )
        self.dept_filter.set("All")
        self.dept_filter.pack(side="left", padx=(0, 15))

        # Search button
        search_btn = ctk.CTkButton(
            filter_inner,
            text="🔍 Filter",
            width=100,
            height=35,
            font=("Roboto", 13, "bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['secondary'],
            command=self.apply_filters
        )
        search_btn.pack(side="left", padx=(0, 10))

        # Clear button
        clear_btn = ctk.CTkButton(
            filter_inner,
            text="🔄 Clear",
            width=100,
            height=35,
            font=("Roboto", 13, "bold"),
            fg_color="gray",
            hover_color="#6b7280",
            command=self.clear_filters
        )
        clear_btn.pack(side="left")

        # Table frame
        table_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True)

        # Treeview styling
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                       background="white",
                       foreground="black",
                       rowheight=35,
                       fieldbackground="white",
                       font=("Roboto", 11))
        style.configure("Treeview.Heading",
                       background=COLORS['primary'],
                       foreground="white",
                       font=("Roboto", 12, "bold"))
        style.map("Treeview", background=[("selected", COLORS['info'])])

        # Create treeview
        tree_container = ctk.CTkFrame(table_frame, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Student ID", "Name", "Department", "Date", "Time", "Status")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="tree headings", height=15)

        # Configure columns
        self.tree.column("#0", width=0, stretch=False)
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Student ID", width=120, anchor="center")
        self.tree.column("Name", width=200, anchor="w")
        self.tree.column("Department", width=180, anchor="center")
        self.tree.column("Date", width=120, anchor="center")
        self.tree.column("Time", width=100, anchor="center")
        self.tree.column("Status", width=100, anchor="center")

        # Configure headings
        for col in columns:
            self.tree.heading(col, text=col, anchor="center")

        # Scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Alternate row colors
        self.tree.tag_configure("evenrow", background="#f8fafc")
        self.tree.tag_configure("oddrow", background="white")
        self.tree.tag_configure("present", foreground=COLORS['success'])

        # Action buttons
        action_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=10)

        delete_btn = ctk.CTkButton(
            action_frame,
            text="🗑️ Delete Selected",
            width=150,
            height=40,
            font=("Roboto", 13, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            corner_radius=8,
            command=self.delete_record
        )
        delete_btn.pack(side="left", padx=(0, 10))

        # Stats label
        self.stats_label = ctk.CTkLabel(
            action_frame,
            text="Total Records: 0",
            font=("Roboto", 13, "bold"),
            text_color=COLORS['primary']
        )
        self.stats_label.pack(side="right")

    def set_today(self):
        """Set date to today and apply filter"""
        self.date_picker.set_date(datetime.now())
        self.apply_filters()

    def set_yesterday(self):
        """Set date to yesterday and apply filter"""
        yesterday = datetime.now() - timedelta(days=1)
        self.date_picker.set_date(yesterday)
        self.apply_filters()

    def load_attendance(self):
        """Load all attendance records"""
        self.attendance_records = db.get_attendance()
        self.display_records(self.attendance_records)

    def display_records(self, records):
        """Display attendance records in treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add records
        for idx, record in enumerate(records):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                record['id'],
                record['student_id'],
                record['name'],
                record['department'] or "N/A",
                format_date(record['date']),
                format_time(record['time']),
                record['status']
            ), tags=(tag, "present"))

        # Update stats
        self.stats_label.configure(text=f"Total Records: {len(records)}")

    def apply_filters(self):
        """Apply filters to attendance records"""
        date = self.date_picker.get_date().strftime("%Y-%m-%d")
        department = self.dept_filter.get()

        date_filter = date if date else None
        dept_filter = department if department != "All" else None

        records = db.get_attendance(date=date_filter, department=dept_filter)
        self.display_records(records)

    def clear_filters(self):
        """Clear all filters"""
        self.date_picker.set_date(datetime.now())
        self.dept_filter.set("All")
        self.load_attendance()

    def delete_record(self):
        """Delete selected attendance record"""
        selected = self.tree.selection()
        if not selected:
            show_toast(self, "Please select a record to delete", "warning")
            return

        values = self.tree.item(selected[0])['values']
        record_id = values[0]
        name = values[2]

        # Confirm deletion
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("400x180")
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

        ctk.CTkLabel(frame, text="⚠️ Confirm Deletion", font=("Roboto", 16, "bold"), text_color=COLORS['danger']).pack(pady=(0, 10))
        ctk.CTkLabel(frame, text=f"Delete attendance record for {name}?", font=("Roboto", 12)).pack(pady=(0, 20))

        def confirm_delete():
            success = db.delete_attendance(record_id)
            if success:
                show_toast(self, "Record deleted successfully", "success")
                confirm_window.destroy()
                self.apply_filters()
            else:
                show_toast(confirm_window, "Failed to delete record", "error")

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        ctk.CTkButton(button_frame, text=" Yes", width=130, height=35, font=("Roboto", 12, "bold"),
                     fg_color=COLORS['danger'], hover_color="#dc2626", command=confirm_delete).pack(side="left", padx=(0, 10))
        ctk.CTkButton(button_frame, text=" No", width=130, height=35, font=("Roboto", 12, "bold"),
                     fg_color="gray", hover_color="#6b7280", command=confirm_window.destroy).pack(side="left")

    def export_to_excel_thread(self):
        """Export attendance to Excel in thread"""
        threading.Thread(target=self.export_attendance, daemon=True).start()

    def export_attendance(self):
        """Export attendance records to Excel"""
        try:
            # Show loading dialog
            loading = None
            self.after(0, lambda: setattr(self, 'loading_dialog', LoadingDialog(self, "Exporting", "Preparing Excel file...")))

            # Get current records
            records = []
            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                records.append([
                    values[1],  # Student ID
                    values[2],  # Name
                    values[3],  # Department
                    values[4],  # Date
                    values[5],  # Time
                    values[6]   # Status
                ])

            if not records:
                self.after(0, lambda: show_toast(self, "No records to export", "warning"))
                return

            # Export to Excel
            filename = f"attendance_{get_current_date().replace('-', '_')}.xlsx"
            headers = ["Student ID", "Name", "Department", "Date", "Time", "Status"]
            filepath = export_to_excel(records, filename, headers)

            # Close loading and show success
            if hasattr(self, 'loading_dialog'):
                self.after(0, lambda: self.loading_dialog.close())

            if filepath:
                self.after(0, lambda: show_toast(self, f"Exported to {filename} ", "success"))
            else:
                self.after(0, lambda: show_toast(self, "Export failed", "error"))

        except Exception as e:
            if hasattr(self, 'loading_dialog'):
                self.after(0, lambda: self.loading_dialog.close())
            self.after(0, lambda: show_toast(self, f"Export error: {str(e)}", "error"))