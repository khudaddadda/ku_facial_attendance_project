import cv2
import numpy as np


class PalmRecognitionModule:
    """Simple demo-level palm recognition module using image preprocessing."""

    def __init__(self):
        self.similarity_threshold = 0.06

    def preprocess_palm(self, frame):
        """
        Preprocess palm image into a simple fixed-size embedding.
        This is a demo-level approach using grayscale normalized image features.
        """
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Crop center region as rough palm area
            h, w = gray.shape
            x1 = int(w * 0.25)
            x2 = int(w * 0.75)
            y1 = int(h * 0.20)
            y2 = int(h * 0.80)

            palm_region = gray[y1:y2, x1:x2]

            if palm_region is None or palm_region.size == 0:
                return None, frame

            # Resize to fixed shape
            palm_region = cv2.resize(palm_region, (64, 64))

            # Normalize
            palm_region = palm_region.astype("float32") / 255.0

            # Flatten as feature vector
            embedding = palm_region.flatten()

            # Normalize vector
            norm = np.linalg.norm(embedding)
            if norm == 0:
                return None, frame

            embedding = embedding / norm

            # Display guide rectangle
            display_frame = frame.copy()
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                display_frame,
                "Place palm inside box and press SPACE",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            return embedding.tolist(), display_frame

        except Exception as e:
            print(f"Palm preprocessing error: {e}")
            return None, frame

    def capture_palm(self, camera_index=1):
        """
        Open webcam and capture palm embedding when SPACE is pressed.
        ESC cancels.
        """
        cap = cv2.VideoCapture(1)

        if not cap.isOpened():
            print("[ERROR] Could not open camera for palm capture")
            return None

        print("[INFO] Palm camera opened. Place palm inside box and press SPACE. ESC to cancel.")

        palm_embedding = None

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            embedding, display_frame = self.preprocess_palm(frame)

            cv2.imshow("Palm Capture", display_frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                break

            if key == 32 and embedding is not None:  # SPACE
                palm_embedding = embedding
                break

        cap.release()
        cv2.destroyAllWindows()
        return palm_embedding

    def compare_palm_embeddings(self, emb1, emb2, threshold=None):
        """
        Compare two palm embeddings using cosine distance.
        Lower distance means more similar.
        """
        try:
            if threshold is None:
                threshold = self.similarity_threshold

            v1 = np.array(emb1, dtype=np.float32)
            v2 = np.array(emb2, dtype=np.float32)

            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 == 0 or norm2 == 0:
                return False, 999.0

            similarity = np.dot(v1, v2) / (norm1 * norm2)
            cosine_distance = 1 - similarity

            is_match = cosine_distance < threshold

            print(f"[PALM MATCH] Distance: {cosine_distance:.4f}, Threshold: {threshold}, Match: {is_match}")
            return is_match, float(cosine_distance)

        except Exception as e:
            print(f"Palm comparison error: {e}")
            return False, 999.0

    def recognize_palm(self, stored_embeddings, camera_index=1):
        """
        Recognize palm against stored embeddings.
        stored_embeddings format:
        [
            {"id": 1, "name": "Ali", "embedding": [...]},
            {"id": 2, "name": "Sara", "embedding": [...]}
        ]
        """
        cap = cv2.VideoCapture(1)

        if not cap.isOpened():
            print("[ERROR] Could not open camera for palm recognition")
            return None

        print("[INFO] Palm recognition started. Place palm inside box and press SPACE. ESC to cancel.")

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            new_embedding, display_frame = self.preprocess_palm(frame)

            cv2.putText(
                display_frame,
                "SPACE = scan | ESC = cancel",
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.imshow("Palm Recognition", display_frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                cap.release()
                cv2.destroyAllWindows()
                return None

            if key == 32:  # SPACE
                if new_embedding is None:
                    print("[WARNING] No valid palm detected")
                    continue

                best_match = None
                best_distance = 999.0

                for person in stored_embeddings:
                    stored_embedding = person.get("embedding")
                    if stored_embedding is None:
                        continue

                    match, distance = self.compare_palm_embeddings(stored_embedding, new_embedding)

                    if match and distance < best_distance:
                        best_distance = distance
                        best_match = person

                cap.release()
                cv2.destroyAllWindows()

                if best_match:
                    print(f"Match found: {best_match.get('name', 'Unknown')} (distance: {best_distance:.4f})")
                    return best_match

                print("No matching palm found")
                return None


# Global instance
palm_recognizer = PalmRecognitionModule()