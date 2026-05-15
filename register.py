import hashlib
import threading
import customtkinter as ctk
from tkinter import messagebox

from config import APP_TITLE, COLORS
from db import db
from utils import center_window, show_toast
from face_recognition_module import face_recognizer
from fingerprint_module import fingerprint_module


class RegisterPage(ctk.CTkFrame):
    """Registration page for creating the first Super Admin and later Admin accounts."""

    def __init__(self, parent, on_success):
        super().__init__(parent, fg_color=COLORS["bg_light"])

        # Parent/app references
        self.parent = parent
        self.master = parent
        self.on_success = on_success

        # Biometric state
        self.face_embedding = None
        self.palm_embedding = None
        self.iris_embedding = None
        self.fingerprint_id = None

        # Track whether face has been captured successfully
        self.captured = False

        # Build UI
        self.create_ui()

    def create_ui(self):
        """Create registration UI"""
        # Scrollable frame container
        scrollable = ctk.CTkScrollableFrame(self, fg_color="transparent", width=600, height=680)
        scrollable.pack(expand=True, fill="both", padx=20, pady=20)

        main_container = ctk.CTkFrame(scrollable, fg_color="transparent")
        main_container.pack(expand=True, fill="both")

        # Title
        title_label = ctk.CTkLabel(
            main_container,
            text="User Registration",
            font=("Roboto", 32, "bold"),
            text_color=COLORS['primary']
        )
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            main_container,
            text="Create your account to access the system",
            font=("Roboto", 14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 10))

        # Form frame
        form_frame = ctk.CTkFrame(
            main_container,
            fg_color="white",
            corner_radius=15,
            border_width=2,
            border_color=COLORS['primary']
        )
        form_frame.pack(padx=40, pady=20)

        form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_inner.pack(padx=40, pady=40)

        # Name field
        ctk.CTkLabel(
            form_inner,
            text="Full Name",
            font=("Roboto", 13, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))

        self.name_entry = ctk.CTkEntry(
            form_inner,
            width=350,
            height=40,
            placeholder_text="Enter your full name",
            font=("Roboto", 13),
            corner_radius=8
        )
        self.name_entry.pack(pady=(0, 15))

        # Username field
        ctk.CTkLabel(
            form_inner,
            text="Username",
            font=("Roboto", 13, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))

        self.username_entry = ctk.CTkEntry(
            form_inner,
            width=350,
            height=40,
            placeholder_text="Choose a username",
            font=("Roboto", 13),
            corner_radius=8
        )
        self.username_entry.pack(pady=(0, 15))

        # Password field
        ctk.CTkLabel(
            form_inner,
            text="Password",
            font=("Roboto", 13, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))

        self.password_entry = ctk.CTkEntry(
            form_inner,
            width=350,
            height=40,
            placeholder_text="Create a password",
            font=("Roboto", 13),
            show="*",
            corner_radius=8
        )
        self.password_entry.pack(pady=(0, 15))

        # Confirm password field
        ctk.CTkLabel(
            form_inner,
            text="Confirm Password",
            font=("Roboto", 13, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))

        self.confirm_password_entry = ctk.CTkEntry(
            form_inner,
            width=350,
            height=40,
            placeholder_text="Confirm your password",
            font=("Roboto", 13),
            show="*",
            corner_radius=8
        )
        self.confirm_password_entry.pack(pady=(0, 20))

        # Capture face button
        self.capture_btn = ctk.CTkButton(
            form_inner,
            text="Capture Face",
            width=350,
            height=45,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['info'],
            hover_color=COLORS['secondary'],
            corner_radius=8,
            command=self.start_face_capture
        )
        self.capture_btn.pack(pady=(0, 10))

        # Face status label
        self.status_label = ctk.CTkLabel(
            form_inner,
            text="",
            font=("Roboto", 12),
            text_color=COLORS['success']
        )
        self.status_label.pack(pady=(0, 15))

        # Fingerprint button
        self.fingerprint_btn = ctk.CTkButton(
            form_inner,
            text="Enroll Fingerprint",
            width=350,
            height=45,
            font=("Roboto", 14, "bold"),
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            corner_radius=8,
            command=self.enroll_fingerprint
        )
        self.fingerprint_btn.pack(pady=(0, 10))

        # Fingerprint status label
        self.fingerprint_status = ctk.CTkLabel(
            form_inner,
            text="Fingerprint: Not enrolled",
            font=("Roboto", 12),
            text_color="gray"
        )
        self.fingerprint_status.pack(pady=(0, 15))

        # Register button
        self.register_btn = ctk.CTkButton(
            form_inner,
            text="Register",
            width=350,
            height=45,
            font=("Roboto", 15, "bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['secondary'],
            corner_radius=8,
            command=self.register_user
        )
        self.register_btn.pack()

        # Already have account label
        login_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        login_frame.pack(pady=(10, 0))

        ctk.CTkLabel(
            login_frame,
            text="Already have an account? ",
            font=("Roboto", 12),
            text_color="gray"
        ).pack(side="left")

        login_link = ctk.CTkLabel(
            login_frame,
            text="Login here",
            font=("Roboto", 12, "bold"),
            text_color=COLORS['primary'],
            cursor="hand2"
        )
        login_link.pack(side="left")
        login_link.bind("<Button-1>", lambda e: self.on_success())

    # ============================================================
    # Face capture
    # ============================================================

    def start_face_capture(self):
        """Start face capture in a separate thread to avoid freezing the UI."""
        self.capture_btn.configure(state="disabled", text="Opening Camera...")
        self.status_label.configure(text="Capturing face...", text_color="orange")

        threading.Thread(target=self.capture_face, daemon=True).start()

    def capture_face(self):
        """Capture face using the existing face recognition module."""
        try:
            face_img = face_recognizer.capture_face()

            if face_img is None:
                self.after(0, self.update_capture_status, False, "Face capture cancelled or failed")
                return

            embedding = face_recognizer.generate_embedding(face_img)

            if embedding is None:
                self.after(0, self.update_capture_status, False, "No face detected")
                return

            self.face_embedding = embedding
            self.captured = True

            self.after(0, self.update_capture_status, True, "Face captured successfully!")

        except Exception as e:
            self.after(0, self.update_capture_status, False, f"Capture error: {e}")

    def update_capture_status(self, success, message):
        """Update face capture status in the UI."""
        if success:
            self.status_label.configure(text=message, text_color="green")
            self.capture_btn.configure(state="normal", text="Capture Face Again")
            show_toast(self, message, "success")
        else:
            self.status_label.configure(text=message, text_color="red")
            self.capture_btn.configure(state="normal", text="Capture Face")
            show_toast(self, message, "error")

    # ============================================================
    # Fingerprint enrollment
    # ============================================================

    def enroll_fingerprint(self):
        """Start fingerprint enrollment in background thread"""

        threading.Thread(
            target=self._enroll_fingerprint_thread,
            daemon=True
        ).start()


    def _enroll_fingerprint_thread(self):

        try:

            self.after(
                0,
                lambda: self.fingerprint_btn.configure(
                    state="disabled",
                    text="Enrolling..."
                )
            )

            self.after(
                0,
                lambda: self.fingerprint_status.configure(
                    text="Starting fingerprint enrollment...",
                    text_color="orange"
                )
            )

            fingerprint_id = db.get_next_fingerprint_id()

            def enrollment_callback(message):

                if message == "ENROLL_START":

                    self.after(
                        0,
                        lambda: show_toast(
                            self,
                            "Fingerprint enrollment started",
                            "info"
                        )
                    )

                elif message == "Place finger":

                    self.after(
                        0,
                        lambda: show_toast(
                            self,
                            "Place finger on sensor",
                            "info"
                        )
                    )

                elif message == "Remove finger":

                    self.after(
                        0,
                        lambda: show_toast(
                            self,
                            "Remove finger",
                            "warning"
                        )
                    )

                elif message == "Place same finger again":

                    self.after(
                        0,
                        lambda: show_toast(
                            self,
                            "Place the same finger again",
                            "info"
                        )
                    )

            success = fingerprint_module.enroll_fingerprint(
                fingerprint_id,
                callback=enrollment_callback
            )

            if success:

                self.fingerprint_id = fingerprint_id

                self.after(
                    0,
                    lambda: self.fingerprint_status.configure(
                        text=f"Fingerprint: Enrolled (ID {fingerprint_id})",
                        text_color="green"
                    )
                )

                self.after(
                    0,
                    lambda: self.fingerprint_btn.configure(
                        state="disabled",
                        text="Fingerprint Enrolled"
                    )
                )

                self.after(
                    0,
                    lambda: show_toast(
                        self,
                        f"Fingerprint enrolled successfully! ID: {fingerprint_id}",
                        "success"
                    )
                )

            else:

                self.after(
                    0,
                    lambda: self.fingerprint_btn.configure(
                        state="normal",
                        text="Enroll Fingerprint"
                    )
                )

                self.after(
                    0,
                    lambda: self.fingerprint_status.configure(
                        text="Fingerprint enrollment failed",
                        text_color="red"
                    )
                )

                self.after(
                    0,
                    lambda: show_toast(
                        self,
                        "Fingerprint enrollment failed",
                        "error"
                    )
                )

        except Exception as e:

            self.after(
                0,
                lambda: self.fingerprint_btn.configure(
                    state="normal",
                    text="Enroll Fingerprint"
                )
            )

            self.after(
                0,
                lambda: show_toast(
                    self,
                    f"Fingerprint enrollment failed: {e}",
                    "error"
                )
            )
    # ============================================================
    # Registration logic
    # ============================================================

    def register_user(self):
        """Validate form and register a new user/admin."""
        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm_password = self.confirm_password_entry.get().strip()

        if not name:
            show_toast(self, "Please enter your full name", "error")
            return

        if not username:
            show_toast(self, "Please enter a username", "error")
            return

        if len(username) < 4:
            show_toast(self, "Username must be at least 4 characters", "error")
            return

        if not password:
            show_toast(self, "Please enter a password", "error")
            return

        if len(password) < 6:
            show_toast(self, "Password must be at least 6 characters", "error")
            return

        if password != confirm_password:
            show_toast(self, "Passwords do not match", "error")
            return

        if not self.captured or self.face_embedding is None:
            show_toast(self, "Please capture your face first", "error")
            return

        user_count = db.get_user_count()

        if user_count > 0:
            current_user = getattr(self.master, "current_user", None)
            if not current_user or current_user.get("role") != "super_admin":
                messagebox.showerror(
                    "Access Denied",
                    "Only Super Admin can create new admin accounts."
                )
                return

        if db.check_user_exists(username):
            show_toast(self, "Username already exists", "error")
            return

        duplicate = db.check_duplicate_face_user(self.face_embedding)
        if duplicate:
            show_toast(
                self,
                f"This face is already registered to user '{duplicate['name']}'",
                "error"
            )
            return

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if user_count == 0:
            role = "super_admin"
        else:
            role = "admin"

        success = db.register_user(
            username=username,
            password=hashed_password,
            name=name,
            role=role,
            face_embedding=self.face_embedding,
            palm_embedding=self.palm_embedding,
            iris_embedding=self.iris_embedding,
            fingerprint_id=self.fingerprint_id
        )

        if success:
            if role == "super_admin":
                show_toast(self, "Super Admin registered successfully!", "success")
            else:
                show_toast(self, "Admin registered successfully!", "success")

            self.after(1500, self.go_to_login)
        else:
            show_toast(self, "Registration failed", "error")

    # ============================================================
    # Navigation
    # ============================================================

    def go_to_login(self):
        """Close registration view and return to login."""
        self.destroy()
        self.on_success()


def show_register_window(on_success):
    """Show registration window."""
    window = ctk.CTk()
    window.title(f"{APP_TITLE} - Register")
    center_window(window, 600, 750)
    window.resizable(False, False)

    RegisterPage(window, on_success).pack(fill="both", expand=True)

    window.mainloop()