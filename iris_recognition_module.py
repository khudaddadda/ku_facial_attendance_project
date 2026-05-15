import cv2
import numpy as np


class IrisRecognizer:
    def __init__(self):
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )
        self.similarity_threshold = 0.08

    def extract_iris_embedding(self, eye_img):
        """
        Extract a simple normalized embedding from one eye region.
        This is simplified eye-region recognition, not full iris segmentation.
        """
        try:
            if eye_img is None or eye_img.size == 0:
                return None

            # Convert to grayscale if needed
            if len(eye_img.shape) == 3:
                gray = cv2.cvtColor(eye_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = eye_img.copy()

            h, w = gray.shape[:2]
            if h < 20 or w < 20:
                return None

            # Resize and normalize
            gray = cv2.resize(gray, (64, 64))
            gray = cv2.equalizeHist(gray)
            gray = gray.astype(np.float32) / 255.0

            # Flatten as simple embedding
            embedding = gray.flatten()

            # Normalize vector
            norm = np.linalg.norm(embedding)
            if norm == 0:
                return None

            embedding = embedding / norm
            return embedding

        except Exception as e:
            print(f"[IRIS EMBEDDING ERROR] {e}")
            return None

    def get_single_eye_crop(self, frame):
        """
        Detect eyes and return one consistent eye crop.
        Chooses the leftmost eye so registration and recognition stay consistent.
        """
        try:
            if frame is None or frame.size == 0:
                return None, None

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            eyes = self.eye_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            if len(eyes) == 0:
                return None, None

            # Sort by x position and always choose leftmost eye
            eyes = sorted(eyes, key=lambda e: e[0])
            x, y, w, h = eyes[0]

            pad = 10
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(frame.shape[1], x + w + pad)
            y2 = min(frame.shape[0], y + h + pad)

            eye_crop = frame[y1:y2, x1:x2]

            if eye_crop is None or eye_crop.size == 0:
                return None, None

            return eye_crop, (x1, y1, x2 - x1, y2 - y1)

        except Exception as e:
            print(f"[EYE DETECTION ERROR] {e}")
            return None, None

    def capture_iris_samples(self, num_samples=3, camera_index=0):
        """
        Capture multiple samples of one eye and average them.
        Press SPACE to capture each sample.
        Press ESC to cancel.
        """
        cap = cv2.VideoCapture(1)

        if not cap.isOpened():
            print("[ERROR] Could not open iris camera")
            return None

        print("[INFO] Iris camera opened. Show the SAME eye clearly and press SPACE. ESC to cancel.")
        samples = []

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            eye_crop, box = self.get_single_eye_crop(frame)

            display = frame.copy()

            if box is not None:
                x, y, w, h = box
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.putText(
                display,
                f"Iris Samples: {len(samples)}/{num_samples}",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.putText(
                display,
                "Show one eye clearly | SPACE = capture | ESC = cancel",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )
            cv2.imshow("Iris Capture", display)
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                cap.release()
                cv2.destroyAllWindows()
                return None

            elif key == 32:  # SPACE
                if eye_crop is not None:
                    emb = self.extract_iris_embedding(eye_crop)
                    if emb is not None:
                        samples.append(emb)
                        print(f"[INFO] Captured iris sample {len(samples)}/{num_samples}")
                    else:
                        print("[WARNING] Invalid eye sample")
                else:
                    print("[WARNING] No eye detected")

                if len(samples) >= num_samples:
                    break

        cap.release()
        cv2.destroyAllWindows()

        final_embedding = np.mean(samples, axis=0)
        norm = np.linalg.norm(final_embedding)
        if norm != 0:
            final_embedding = final_embedding / norm

        return final_embedding

    def compare_iris_embeddings(self, stored_embedding, new_embedding):
        """
        Compare stored and new embeddings using cosine distance.
        Lower distance = more similar.
        """
        try:
            if stored_embedding is None or new_embedding is None:
                return False, 1.0

            stored_embedding = np.array(stored_embedding, dtype=np.float32)
            new_embedding = np.array(new_embedding, dtype=np.float32)

            # Normalize both
            stored_norm = np.linalg.norm(stored_embedding)
            new_norm = np.linalg.norm(new_embedding)

            if stored_norm == 0 or new_norm == 0:
                return False, 1.0

            stored_embedding = stored_embedding / stored_norm
            new_embedding = new_embedding / new_norm

            cosine_similarity = np.dot(stored_embedding, new_embedding)
            cosine_distance = 1 - cosine_similarity

            match = cosine_distance < self.similarity_threshold
            print(
                f"[IRIS MATCH] Distance: {cosine_distance:.4f}, "
                f"Threshold: {self.similarity_threshold}, Match: {match}"
            )

            return match, cosine_distance

        except Exception as e:
            print(f"[IRIS COMPARE ERROR] {e}")
            return False, 1.0

    def recognize_iris(self, stored_embeddings, camera_index=0):
        """
        Recognize one eye against stored embeddings.
        stored_embeddings format example:
        [
            {"id": 1, "name": "Ali", "embedding": [...]},
            {"id": 2, "name": "Sara", "embedding": [...]}
        ]
        """
        cap = cv2.VideoCapture(1)

        if not cap.isOpened():
            print("[ERROR] Could not open iris camera")
            return None

        print("[INFO] Iris recognition started. Show one eye clearly. Press SPACE to scan, ESC to cancel.")

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            eye_crop, box = self.get_single_eye_crop(frame)
            display = frame.copy()

            if box is not None:
                x, y, w, h = box
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.putText(
                display,
                "SPACE = scan | ESC = cancel",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.imshow("Iris Recognition", display)
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                cap.release()
                cv2.destroyAllWindows()
                return None

            elif key == 32:  # SPACE
                if eye_crop is None:
                    print("[WARNING] No eye detected")
                    continue

                new_embedding = self.extract_iris_embedding(eye_crop)

                if new_embedding is None:
                    print("[WARNING] Could not extract iris embedding")
                    continue

                best_match = None
                best_distance = 1.0

                for person in stored_embeddings:
                    stored_embedding = person.get("embedding")
                    if stored_embedding is None:
                        continue

                    match, distance = self.compare_iris_embeddings(
                        stored_embedding,
                        new_embedding
                    )

                    if match and distance < best_distance:
                        best_distance = distance
                        best_match = person

                cap.release()
                cv2.destroyAllWindows()

                if best_match:
                    print(
                        f"Match found: {best_match.get('name', 'Unknown')} "
                        f"(distance: {best_distance:.4f})"
                    )
                    return best_match

                print("No matching iris found")
                return None