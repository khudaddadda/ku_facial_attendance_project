import pymysql
from pymysql import Error
import json
from datetime import datetime, timedelta
from config import (
    DB_CONFIG, TABLE_USERS, TABLE_STUDENTS, 
    TABLE_ATTENDANCE, TABLE_FACE_EMBEDDINGS
)



class Database:
    """Database handler class for MySQL operations"""

    def __init__(self):
        self.connection = None
        self.create_database()
        self.connect()
        self.create_tables()

    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            connection = pymysql.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                port=DB_CONFIG['port']
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            cursor.close()
            connection.close()
            print(f" Database '{DB_CONFIG['database']}' ready")
        except Error as e:
            print(f" Error creating database: {e}")

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                port=DB_CONFIG['port'],
                autocommit=True
            )
            print(" Database connected successfully")
        except Error as e:
            print(f" Error connecting to database: {e}")
            self.connection = None

    def create_tables(self):
        """Create all required tables"""
        if not self.connection:
            return

        cursor = self.connection.cursor()

        # Users table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_USERS} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                face_embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Students table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_STUDENTS} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                roll_no VARCHAR(50) UNIQUE NOT NULL,
                department VARCHAR(100) NOT NULL,
                year VARCHAR(20) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(20),
                photo_path TEXT,
                face_embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Attendance table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_ATTENDANCE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                department VARCHAR(100),
                date DATE NOT NULL,
                time TIME NOT NULL,
                status VARCHAR(20) DEFAULT 'Present',
                marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES {TABLE_STUDENTS}(student_id) ON DELETE CASCADE
            )
        """)

        # Face embeddings table (for multiple samples per student)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_FACE_EMBEDDINGS} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) NOT NULL,
                embedding TEXT NOT NULL,
                sample_index INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES {TABLE_STUDENTS}(student_id) ON DELETE CASCADE
            )
        """)

        cursor.close()
        print(" All tables created successfully")

    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f" Query error: {e}")
            return None

    def execute_update(self, query, params=None):
        """Execute an update/insert/delete query"""
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f" Update error: {e}")
            return False

    # ========== User Management ==========
    
    def check_user_exists(self):
        """Check if any user exists in the system"""
        query = f"SELECT COUNT(*) as count FROM {TABLE_USERS}"
        result = self.execute_query(query)
        return result[0]['count'] > 0 if result else False

    def register_user(self, username, password, name, face_embedding):
        """Register a new user"""
        query = f"""
            INSERT INTO {TABLE_USERS} (username, password, name, face_embedding)
            VALUES (%s, %s, %s, %s)
        """
        return self.execute_update(query, (username, password, name, json.dumps(face_embedding)))

    def verify_user(self, username, password):
        """Verify user credentials"""
        query = f"SELECT * FROM {TABLE_USERS} WHERE username = %s AND password = %s"
        result = self.execute_query(query, (username, password))
        return result[0] if result else None

    def get_all_users(self):
        """Get all users with face embeddings"""
        query = f"SELECT id, username, name, face_embedding FROM {TABLE_USERS}"
        return self.execute_query(query)

    # ========== Face Duplicate Checking ==========
    
    def check_duplicate_face_user(self, face_embedding):
        """Check if face embedding already exists for any user"""
        from face_recognition_module import face_recognizer

        query = f"SELECT id, username, name, face_embedding FROM {TABLE_USERS}"
        all_users = self.execute_query(query)

        if not all_users:
            return None

        for user in all_users:
            if user['face_embedding']:
                stored_embedding = json.loads(user['face_embedding'])
                is_match, distance = face_recognizer.compare_embeddings(face_embedding, stored_embedding)
                if is_match:
                    return {
                        'id': user['id'],
                        'username': user['username'],
                        'name': user['name'],
                        'distance': distance
                    }
        return None

    def check_duplicate_face_student(self, face_embedding):
        """Check if face embedding already exists for any student"""
        from face_recognition_module import face_recognizer

        query = f"SELECT id, student_id, name, roll_no, face_embedding FROM {TABLE_STUDENTS}"
        all_students = self.execute_query(query)

        if not all_students:
            return None

        for student in all_students:
            if student['face_embedding']:
                stored_embedding = json.loads(student['face_embedding'])
                is_match, distance = face_recognizer.compare_embeddings(face_embedding, stored_embedding)
                if is_match:
                    return {
                        'id': student['id'],
                        'student_id': student['student_id'],
                        'name': student['name'],
                        'roll_no': student['roll_no'],
                        'distance': distance
                    }
        return None

    # ========== Student Management ==========
    
    def add_student(self, student_id, name, roll_no, department, year, email, phone, photo_path, face_embedding):
        """Add a new student"""
        query = f"""
            INSERT INTO {TABLE_STUDENTS} (student_id, name, roll_no, department, year, email, phone, photo_path, face_embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_update(query, (student_id, name, roll_no, department, year, email, phone, photo_path, json.dumps(face_embedding)))

    def update_student(self, id, name, roll_no, department, year, email, phone):
        """Update student information"""
        query = f"""
            UPDATE {TABLE_STUDENTS}
            SET name = %s, roll_no = %s, department = %s, year = %s, email = %s, phone = %s
            WHERE id = %s
        """
        return self.execute_update(query, (name, roll_no, department, year, email, phone, id))

    def delete_student(self, id):
        """Delete a student"""
        query = f"DELETE FROM {TABLE_STUDENTS} WHERE id = %s"
        return self.execute_update(query, (id,))

    def get_all_students(self):
        """Get all students"""
        query = f"SELECT * FROM {TABLE_STUDENTS} ORDER BY name"
        return self.execute_query(query)

    def search_students(self, search_term, search_by='name'):
        """Search students by name, roll_no, or department"""
        query = f"SELECT * FROM {TABLE_STUDENTS} WHERE {search_by} LIKE %s ORDER BY name"
        return self.execute_query(query, (f'%{search_term}%',))

    def get_student_by_id(self, student_id):
        """Get student by student_id"""
        query = f"SELECT * FROM {TABLE_STUDENTS} WHERE student_id = %s"
        result = self.execute_query(query, (student_id,))
        return result[0] if result else None

    # ========== Multiple Face Embeddings ==========
    
    def add_multiple_face_embeddings(self, student_id, embeddings_list):
        """Add multiple face embeddings for a student"""
        for idx, emb in enumerate(embeddings_list):
            query = f"""
                INSERT INTO {TABLE_FACE_EMBEDDINGS} (student_id, embedding, sample_index)
                VALUES (%s, %s, %s)
            """
            self.execute_update(query, (student_id, json.dumps(emb), idx))
        return True

    def get_all_student_embeddings_advanced(self):
        """Get all student embeddings (multiple per student) for high accuracy"""
        students = self.get_all_students()
        result = {}
        
        for student in students:
            student_id = student['student_id']
            
            # Try to get multiple embeddings from new table
            query = f"""
                SELECT embedding FROM {TABLE_FACE_EMBEDDINGS}
                WHERE student_id = %s ORDER BY sample_index
            """
            embeddings_result = self.execute_query(query, (student_id,))
            
            embeddings_list = []
            if embeddings_result:
                for row in embeddings_result:
                    try:
                        embeddings_list.append(json.loads(row['embedding']))
                    except:
                        pass
            
            # If no embeddings in new table, use old one
            if not embeddings_list and student['face_embedding']:
                try:
                    embeddings_list.append(json.loads(student['face_embedding']))
                except:
                    pass
            
            if embeddings_list:
                result[student_id] = {
                    'name': student['name'],
                    'department': student['department'],
                    'roll_no': student['roll_no'],
                    'embeddings': embeddings_list
                }
        
        return result

    # ========== Attendance Management ==========
    
    def mark_attendance(self, student_id, name, department, date, time, status='Present'):
        """Mark attendance for a student"""
        check_query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE student_id = %s AND date = %s"
        existing = self.execute_query(check_query, (student_id, date))

        if existing:
            return False, "Attendance already marked today"

        query = f"""
            INSERT INTO {TABLE_ATTENDANCE} (student_id, name, department, date, time, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        success = self.execute_update(query, (student_id, name, department, date, time, status))
        return success, "Attendance marked successfully" if success else "Failed to mark attendance"

    def get_attendance(self, date=None, department=None, name=None):
        """Get attendance records with optional filters"""
        query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE 1=1"
        params = []

        if date:
            query += " AND date = %s"
            params.append(date)
        if department:
            query += " AND department LIKE %s"
            params.append(f'%{department}%')
        if name:
            query += " AND name LIKE %s"
            params.append(f'%{name}%')

        query += " ORDER BY date DESC, time DESC"
        return self.execute_query(query, tuple(params))

    def get_today_attendance(self):
        """Get today's attendance"""
        today = datetime.now().date()
        return self.get_attendance(date=today)

    def get_attendance_stats(self):
        """Get attendance statistics"""
        today = datetime.now().date()

        total_query = f"SELECT COUNT(*) as count FROM {TABLE_STUDENTS}"
        total = self.execute_query(total_query)
        total_students = total[0]['count'] if total else 0

        present_query = f"SELECT COUNT(*) as count FROM {TABLE_ATTENDANCE} WHERE date = %s"
        present = self.execute_query(present_query, (today,))
        present_today = present[0]['count'] if present else 0

        return {
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': total_students - present_today
        }

    def get_attendance_trend(self, days=7):
        """Get attendance trend for last N days"""
        total_students = self.get_attendance_stats()['total_students']
        
        query = f"""
            SELECT DATE(date) as attendance_date, COUNT(DISTINCT student_id) as present_count
            FROM {TABLE_ATTENDANCE}
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
            GROUP BY DATE(date)
            ORDER BY attendance_date ASC
        """
        result = self.execute_query(query)
        
        attendance_dict = {}
        if result:
            for row in result:
                attendance_dict[row['attendance_date']] = row['present_count']
        
        trend_data = []
        current_date = datetime.now().date() - timedelta(days=days-1)
        
        for i in range(days):
            date = current_date + timedelta(days=i)
            count = attendance_dict.get(date, 0)
            percentage = (count / total_students * 100) if total_students > 0 else 0
            
            trend_data.append({
                'date': date,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        return trend_data

    def delete_attendance(self, id):
        """Delete an attendance record"""
        query = f"DELETE FROM {TABLE_ATTENDANCE} WHERE id = %s"
        return self.execute_update(query, (id,))

    def clear_all_attendance(self):
        """Clear all attendance records"""
        query = f"TRUNCATE TABLE {TABLE_ATTENDANCE}"
        return self.execute_update(query)

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print(" Database connection closed")


# Global database instance
db = Database()