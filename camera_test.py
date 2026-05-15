import cv2

for index in range(3):
    print(f"Testing camera index {index}...")
    cap = cv2.VideoCapture(index)

    if cap.isOpened():
        print(f"Camera {index} opened")

        ret, frame = cap.read()
        if ret:
            cv2.imshow(f"Camera index {index}", frame)
            cv2.waitKey(2000)

        cap.release()

cv2.destroyAllWindows()