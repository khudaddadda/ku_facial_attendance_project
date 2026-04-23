import cv2
import numpy as np
import os
import tempfile
import time
from deepface import DeepFace
from config import (
    DEEPFACE_MODEL, DEEPFACE_DETECTOR, FACE_MATCH_THRESHOLD,
    RECOGNITION_BUFFER_SIZE, MIN_CONFIRMATIONS, CHECK_INTERVAL
)


class FaceRecognitionModule:
    """Face recognition handler using DeepFace - High Accuracy Version"""

    def __init__(self):
        self.model_name = DEEPFACE_MODEL
        self.detector_backend = DEEPFACE_DETECTOR
        self.threshold = FACE_MATCH_THRESHOLD

    def preprocess_face(self, image):
        """Improve image quality before recognition"""
        try:
            if image is None:
                return None
            
            img = image.copy()
            
            # Histogram equalization for better lighting
            if len(img.shape) == 3:
                try:
                    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
                    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
                    img = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
                except:
                    pass
            
            # Slight blur to reduce noise
            img = cv2.GaussianBlur(img, (3, 3), 0)
            
            return img
        except Exception as e:
            print(f"Preprocess warning: {e}")
            return image

    def capture_face(self, save_path=None):
        """Capture face from webcam and save ONLY the cropped face"""
        cap = cv2.VideoCapture(1)  # FIXED: Changed from 1 to 0
        
        if not cap.isOpened():
            print("Cannot open camera")
            return None

        print("Camera opened. Press SPACE to capture or ESC to cancel")
        captured_face = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            processed_frame = self.preprocess_face(frame)

            # Draw instructions
            cv2.putText(processed_frame, "Press SPACE to capture, ESC to cancel", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Try to detect face
            try:
                face_objs = DeepFace.extract_faces(
                    processed_frame,
                    detector_backend=self.detector_backend,
                    enforce_detection=True
                )

                if face_objs and len(face_objs) > 0:
                    for face_obj in face_objs:
                        facial_area = face_obj['facial_area']
                        x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
                        
                        # Draw rectangle
                        cv2.rectangle(processed_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(processed_frame, "Face Detected", (x, y-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        # Crop the face only
                        captured_face = frame[y:y+h, x:x+w].copy()
                else:
                    cv2.putText(processed_frame, "No Face Detected", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            except:
                pass

            cv2.imshow('Capture Face', processed_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 32:  # SPACE key
                if captured_face is not None:
                    print("Face captured!")
                    
                    # Save ONLY the cropped face
                    if save_path:
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        cv2.imwrite(save_path, captured_face)
                        print(f"Cropped face saved to: {save_path}")
                    break
                else:
                    print("No face detected! Please look at camera.")
            elif key == 27:  # ESC key
                print("Capture cancelled")
                break

        cap.release()
        cv2.destroyAllWindows()

        return captured_face

    def generate_embedding(self, image):
        """Generate face embedding from image"""
        try:
            # If image is a file path
            if isinstance(image, str):
                embedding_objs = DeepFace.represent(
                    img_path=image,
                    model_name=self.model_name,
                    detector_backend=self.detector_backend,
                    enforce_detection=True
                )
            else:
                # If image is numpy array (camera frame)
                processed_image = self.preprocess_face(image)
                
                # Save temporarily
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                    temp_path = tmp_file.name
                    cv2.imwrite(temp_path, processed_image)
                
                try:
                    embedding_objs = DeepFace.represent(
                        img_path=temp_path,
                        model_name=self.model_name,
                        detector_backend=self.detector_backend,
                        enforce_detection=True
                    )
                finally:
                    # Delete temporary file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

            if embedding_objs and len(embedding_objs) > 0:
                embedding = embedding_objs[0]['embedding']
                print(f"Embedding generated (dimension: {len(embedding)})")
                return embedding
            else:
                print("No face detected in image")
                return None
                
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    def extract_face(self, frame):
        try:
            import tempfile
            import os
            import cv2
            from deepface import DeepFace

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                temp_path = tmp.name

            cv2.imwrite(temp_path, frame)

            faces = DeepFace.extract_faces(
                img_path=temp_path,
                detector_backend="mtcnn",
                enforce_detection=False
            )

            os.remove(temp_path)

            if not faces:
                return None

            # Choose the largest detected face
            best_face = None
            best_area = 0

            for face_obj in faces:
                facial_area = face_obj.get("facial_area", {})
                w = facial_area.get("w", 0)
                h = facial_area.get("h", 0)
                area = w * h

                if area > best_area:
                    best_area = area
                    best_face = face_obj

            if best_face is None:
                return None

            extracted_face = best_face["face"]

            # DeepFace returns normalized float image sometimes; convert to uint8
            if extracted_face is not None:
                if extracted_face.max() <= 1.0:
                    extracted_face = (extracted_face * 255).astype("uint8")
                else:
                    extracted_face = extracted_face.astype("uint8")

            return extracted_face

        except Exception as e:
            print("extract_face error:", e)
            return None

    def compare_embeddings(self, embedding1, embedding2):
        try:
            emb1 = np.array(embedding1, dtype=np.float64)
            emb2 = np.array(embedding2, dtype=np.float64)
            
            emb1 = emb1 / (np.linalg.norm(emb1) + 1e-8)
            emb2 = emb2 / (np.linalg.norm(emb2) + 1e-8)
            
            cosine_sim = np.dot(emb1, emb2)
            cosine_dist = 1 - cosine_sim
            
            # Use threshold from config
            threshold = self.threshold
            
            is_match = cosine_dist < threshold
            
            print(f"[FACE MATCH] Distance: {cosine_dist:.4f}, Threshold: {threshold}, Match: {is_match}")
            
            return is_match, cosine_dist
        except Exception as e:
            print(f"Error: {e}")
            return False, 1.0
        
    def capture_multiple_faces(self, num_samples=5):
        import cv2
        import numpy as np
        import time

        embeddings = []
        cap = cv2.VideoCapture(1)

        if not cap.isOpened():
            print("[ERROR] Cannot open camera")
            return None, []

        print("[INFO] Camera opened. Press SPACE to capture each sample, ESC to cancel.")

        while len(embeddings) < num_samples:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            display = frame.copy()

            face_region = self.extract_face(frame)

            msg = f"Samples: {len(embeddings)}/{num_samples}"
            cv2.putText(display, msg, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            if face_region is not None:
                cv2.putText(display, "Face detected - Press SPACE", (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                cv2.putText(display, "No face detected", (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.imshow("Capture Multiple Faces", display)
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                break

            if key == 32:  # SPACE
                if face_region is not None:
                    emb = self.generate_embedding(face_region)
                    if emb is not None:
                        embeddings.append(emb)
                        print(f"[INFO] Captured sample {len(embeddings)}/{num_samples}")
                        time.sleep(0.5)

        cap.release()
        cv2.destroyAllWindows()

        if not embeddings:
            return None, []

        avg_embedding = np.mean(np.array(embeddings), axis=0).tolist()
        return avg_embedding, embeddings
    
    def find_matching_face(self, test_embedding, database_students):
        """Fixed: supports both single embedding and multiple embeddings"""
        
        best_match = None
        best_distance = float('inf')

        for student_id, student_data in database_students.items():

            # ✅ Handle BOTH cases
            if isinstance(student_data, dict):
                embeddings_list = student_data.get('embeddings', [])
            else:
                # 👉 If it's a single embedding (list), wrap it
                embeddings_list = [student_data]

            for stored_embedding in embeddings_list:
                is_match, distance = self.compare_embeddings(test_embedding, stored_embedding)

                if is_match and distance < best_distance:
                    best_distance = distance
                    best_match = student_id

        if best_match:
            print(f"Match found: {best_match} (distance: {best_distance:.4f})")
        else:
            print("No matching face found")

        return best_match, best_distance

    def detect_and_mark_attendance(self, database_students, mark_callback):
        """
        Detect faces and mark attendance with temporal smoothing
        database_students: dict with student_id as key and embeddings list as value
        mark_callback: function to call when face is recognized
        """
        cap = cv2.VideoCapture(1)  # FIXED: Changed from 1 to 0

        if not cap.isOpened():
            print("ERROR: Cannot open camera. Please check camera connection.")
            return 0

        print("Attendance marking active. Press ESC to stop")
        print(f"Loaded {len(database_students)} students for recognition")

        marked_students = set()
        frame_count = 0
        
        # Temporal smoothing buffer
        recognition_buffer = {}
        
        # Initialize buffer for all students
        for student_id in database_students.keys():
            recognition_buffer[student_id] = []

        while True:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Failed to capture frame")
                break

            frame = cv2.flip(frame, 1)
            processed_frame = self.preprocess_face(frame)

            # Draw UI
            cv2.putText(processed_frame, "Attendance Marking Active - Press ESC to stop", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(processed_frame, f"Marked: {len(marked_students)} students", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            frame_count += 1

            # Check face periodically
            if frame_count % CHECK_INTERVAL == 0:
                try:
                    embedding = self.generate_embedding(processed_frame)

                    if embedding:
                        match_id, distance = self.find_matching_face(embedding, database_students)

                        # Update buffer for all students
                        for student_id in database_students.keys():
                            is_match_this_frame = (match_id == student_id)
                            recognition_buffer[student_id].append(1 if is_match_this_frame else 0)
                            
                            # Keep only last N frames
                            if len(recognition_buffer[student_id]) > RECOGNITION_BUFFER_SIZE:
                                recognition_buffer[student_id].pop(0)
                            
                            # Check for confirmation
                            confirmed_matches = sum(recognition_buffer[student_id])
                            
                            if confirmed_matches >= MIN_CONFIRMATIONS and student_id not in marked_students:
                                success = mark_callback(student_id)
                                if success:
                                    marked_students.add(student_id)
                                    print(f"Confirmed attendance for: {student_id}")
                                    
                                    # Show success on frame
                                    cv2.putText(processed_frame, f"Marked: {student_id}", 
                                               (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                    cv2.imshow('Attendance Marking', processed_frame)
                                    cv2.waitKey(1000)

                except Exception as e:
                    print(f"Frame processing error: {e}")

            cv2.imshow('Attendance Marking', processed_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break

        cap.release()
        cv2.destroyAllWindows()

        print(f"Attendance marking completed. Total marked: {len(marked_students)}")
        return len(marked_students)


# Global face recognition instance
face_recognizer = FaceRecognitionModule()