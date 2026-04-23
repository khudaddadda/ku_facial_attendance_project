import customtkinter as ctk
import sys
from config import APP_TITLE, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
from utils import ensure_directories, center_window
from db import db
from register import RegisterPage
from login import LoginPage
from dashboard import Dashboard



class AttendanceApp(ctk.CTk):
    """Main application window - Entry point of the system"""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)

        # Get screen size for responsive window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Set initial size to 80% of screen (responsive)
        init_width = min(int(screen_width * 0.8), DEFAULT_WINDOW_WIDTH)
        init_height = min(int(screen_height * 0.8), DEFAULT_WINDOW_HEIGHT)
        init_width = max(init_width, MIN_WINDOW_WIDTH)
        init_height = max(init_height, MIN_WINDOW_HEIGHT)

        self.geometry(f"{init_width}x{init_height}")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Set theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Create necessary directories
        ensure_directories()
        
        # Center window on screen
        center_window(self, self.winfo_width(), self.winfo_height())

        # Current frame reference
        self.current_frame = None

        # Check if any user exists
        if not db.check_user_exists():
            print("No users found. Showing registration page...")
            self.show_register()
        else:
            print("Users found. Showing login page...")
            self.show_login()

    def clear_frame(self):
        """Clear current frame"""
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

    def show_register(self):
        """Show registration page"""
        self.clear_frame()
        self.current_frame = RegisterPage(self, self.show_login)
        self.current_frame.pack(fill="both", expand=True)

    def show_login(self):
        """Show login page"""
        self.clear_frame()
        self.current_frame = LoginPage(self, self.show_dashboard, self.show_register)
        self.current_frame.pack(fill="both", expand=True)

    def show_dashboard(self, user_data):
        """Show main dashboard"""
        self.clear_frame()
        self.current_frame = Dashboard(self, user_data, self.show_login)
        self.current_frame.pack(fill="both", expand=True)

    def on_closing(self):
        """Handle window close event"""
        db.close()
        self.destroy()
        sys.exit(0)


def main():
    """Main function to run the application"""
    print("=" * 60)
    print("Face Recognition-Based Student Attendance System")
    print("Powered by Python, CustomTkinter, OpenCV, and DeepFace")
    print("=" * 60)
    print()

    try:
        app = AttendanceApp()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user")
        db.close()
        sys.exit(0)
    except Exception as e:
        print(f" Application error: {e}")
        db.close()
        sys.exit(1)


if __name__ == "__main__":
    main()