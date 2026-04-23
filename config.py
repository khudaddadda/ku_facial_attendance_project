# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Khudadad034',  # Change this to your MySQL password
    'database': 'kuzk_face',
    'port': 3306
}

# Application Settings
APP_TITLE = "Face Recognition Attendance System"
APP_VERSION = "1.0.0"

# Responsive Window Settings
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 680

# Theme Colors (Modern & Professional)
COLORS = {
    'primary': '#2563eb',      # Blue
    'secondary': '#7c3aed',    # Purple
    'success': '#10b981',      # Green
    'danger': '#ef4444',       # Red
    'warning': '#f59e0b',      # Orange
    'info': '#06b6d4',         # Teal
    'dark': '#1e293b',         # Dark Blue
    'light': '#f8fafc',        # Light Gray
    'bg_dark': '#0f172a',      # Dark Background
    'bg_light': '#ffffff'      # Light Background
}

# Paths for file storage
IMAGES_PATH = "images/"
ENCODINGS_PATH = "encodings/"
REPORTS_PATH = "attendance_reports/"

# Face Recognition Settings - High Accuracy (>90%)
FACE_DETECTION_CONFIDENCE = 0.6
FACE_MATCH_THRESHOLD = 0.35
DEEPFACE_MODEL = 'VGG-Face'  # High accuracy model
DEEPFACE_DETECTOR = 'mtcnn'  # Best face detector

# Recognition Settings for accuracy
RECOGNITION_BUFFER_SIZE = 10  # Number of frames to buffer
MIN_CONFIRMATIONS = 5         # Minimum matches needed
NUM_FACE_SAMPLES = 3          # Number of face samples per student
CHECK_INTERVAL = 10           # Check face every N frames

# Database Table Names
TABLE_USERS = 'users'
TABLE_STUDENTS = 'students'
TABLE_ATTENDANCE = 'attendance'
TABLE_FACE_EMBEDDINGS = 'student_face_embeddings'

# UI Settings
FONT_FAMILY = 'Roboto'
FONT_SIZE_NORMAL = 13
FONT_SIZE_HEADING = 20
FONT_SIZE_TITLE = 24
BUTTON_HEIGHT = 40
ENTRY_HEIGHT = 35