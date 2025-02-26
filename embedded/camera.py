import time
import cv2

CAMERA_INDEX = 0

def camera_thread(camera_event_flag, frames_queue):
    video_capture = cv2.VideoCapture(CAMERA_INDEX)
    while True:
        
        while not camera_event_flag.is_set():
            pass
        # Limpa o buffer da câmera
        for _ in range(30):  # Lê e descarta 5 frames para evitar atraso
            video_capture.read()
        
        ret, frame = video_capture.read()
        if not ret:
            print("Frame error")
            break
        frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        frames_queue.put(frame)
        camera_event_flag.clear()
        time.sleep(0.3)