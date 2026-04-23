import customtkinter as ctk
import hashlib
import threading
import json
from config import COLORS, APP_TITLE
from utils import show_toast, center_window
from face_recognition_module import face_recognizer
from db import db


class LoginPage(ctk.CTkFrame):
    """Login page with manual and face login options"""

    def __init__(self, parent, on_success, on_register):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.on_success = on_success
        self.on_register = on_register
        self.create_ui()

    def create_ui(self):
        """Create login UI - Fully responsive"""
        # Main container with relative positioning
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title_label = ctk.CTkLabel(
            main_container,
            text="Attendance System",
            font=("Roboto", 36, "bold"),
            text_color=COLORS['primary']
        )
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            main_container,
            text="Face Recognition-Based Student Attendance",
            font=("Roboto", 14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 30))

        # Login form frame
        form_frame = ctk.CTkFrame(
            main_container,
            fg_color="white",
            corner_radius=15,
            border_width=2,
            border_color=COLORS['primary']
        )
        form_frame.pack(padx=40, pady=20)

        form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_inner.pack(padx=50, pady=40)

        # Login type label
        ctk.CTkLabel(
            form_inner,
            text="Login to your account",
            font=("Roboto", 18, "bold"),
            text_color=COLORS['dark']
        ).pack(pady=(0, 20))

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
            placeholder_text="Enter your username",
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
            placeholder_text="Enter your password",
            font=("Roboto", 13),
            show="*",
            corner_radius=8
        )
        self.password_entry.pack(pady=(0, 25))

        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self.manual_login())

        # Manual login button
        self.login_btn = ctk.CTkButton(
            form_inner,
            text="Login",
            width=350,
            height=45,
            font=("Roboto", 15, "bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['secondary'],
            corner_radius=8,
            command=self.manual_login
        )
        self.login_btn.pack(pady=(0, 15))

        # Divider
        divider_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        divider_frame.pack(fill="x", pady=15)

        ctk.CTkFrame(divider_frame, height=1, fg_color="lightgray").pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(divider_frame, text="OR", font=("Roboto", 12), text_color="gray").pack(side="left")
        ctk.CTkFrame(divider_frame, height=1, fg_color="lightgray").pack(side="left", fill="x", expand=True, padx=(10, 0))

        # Face login button
        self.face_login_btn = ctk.CTkButton(
            form_inner,
            text="Login with Face",
            width=350,
            height=45,
            font=("Roboto", 15, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['info'],
            corner_radius=8,
            command=self.face_login_thread
        )
        self.face_login_btn.pack()

        # Register link
        register_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        register_frame.pack(pady=(15, 0))

        ctk.CTkLabel(
            register_frame,
            text="Don't have an account? ",
            font=("Roboto", 12),
            text_color="gray"
        ).pack(side="left")

        register_link = ctk.CTkLabel(
            register_frame,
            text="Register here",
            font=("Roboto", 12, "bold"),
            text_color=COLORS['primary'],
            cursor="hand2"
        )
        register_link.pack(side="left")
        register_link.bind("<Button-1>", lambda e: self.on_register())

    def manual_login(self):
        """Handle manual login with username and password"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            show_toast(self, "Please enter username and password", "error")
            return

        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Verify credentials
        user = db.verify_user(username, hashed_password)

        if user:
            show_toast(self, f"Welcome back, {user['name']}!", "success")
            self.after(1500, lambda: self.on_success(user))
        else:
            show_toast(self, "Invalid username or password", "error")

    def face_login_thread(self):
        """Start face login in separate thread"""
        self.face_login_btn.configure(state="disabled", text="Opening camera...")
        self.login_btn.configure(state="disabled")
        threading.Thread(target=self.face_login, daemon=True).start()

    def face_login(self):
        """Handle face-based login"""
        try:
            # Get all users with embeddings
            users = db.get_all_users()

            if not users:
                self.after(0, self.update_face_login_status, False, "No registered users found")
                return

            # Create database of embeddings
            database_embeddings = {}
            for user in users:
                if user['face_embedding']:
                    try:
                        embedding = json.loads(user['face_embedding'])
                        database_embeddings[user['username']] = embedding
                    except:
                        pass

            if not database_embeddings:
                self.after(0, self.update_face_login_status, False, "No face data found")
                return

            # Open camera
            import cv2
            cap = cv2.VideoCapture(1)
            
            if not cap.isOpened():
                self.after(0, self.update_face_login_status, False, "Cannot open camera")
                return
            
            self.after(0, self.update_face_login_status, False, "Looking at camera...")
            
            # Capture one frame
            frames = []

            import time
            for _ in range(10):
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                time.sleep(0.1)

            cap.release()
            
            if not ret:
                self.after(0, self.update_face_login_status, False, "Failed to capture image")
                return
            
            # Generate embedding from captured frame
            embedding = face_recognizer.generate_embedding(frame)
            
            if embedding is None:
                self.after(0, self.update_face_login_status, False, "No face detected")
                return
            
            # Find matching user
            matched_username, distance = face_recognizer.find_matching_face(embedding, database_embeddings)

            if matched_username:
                # Get user details
                user = next((u for u in users if u['username'] == matched_username), None)
                if user:
                    self.after(0, self.update_face_login_status, True, f"Welcome, {user['name']}!", user)
                else:
                    self.after(0, self.update_face_login_status, False, "User not found")
            else:
                self.after(0, self.update_face_login_status, False, "Face not recognized")

        except Exception as e:
            self.after(0, self.update_face_login_status, False, f"Error: {str(e)}")

    def update_face_login_status(self, success, message, user=None):
        """Update face login status"""
        self.face_login_btn.configure(state="normal", text="Login with Face")
        self.login_btn.configure(state="normal")

        if success and user:
            show_toast(self, message, "success")
            self.after(1500, lambda: self.on_success(user))
        else:
            show_toast(self, message, "error")


def show_login_window(on_success, on_register):
    """Show login window"""
    window = ctk.CTk()
    window.title(f"{APP_TITLE} - Login")
    center_window(window, 600, 700)
    window.resizable(False, False)

    LoginPage(window, on_success, on_register).pack(fill="both", expand=True)

    window.mainloop()