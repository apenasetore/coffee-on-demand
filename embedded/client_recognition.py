from collections import defaultdict
import time
import cv2
import face_recognition
import os
import pickle

def generate_new_encodings():
    image = face_recognition.load_image_file("henrique.JPG")
    face_encodings = face_recognition.face_encodings(image)

    known_face_encodings = []
    known_face_names = []

    if face_encodings:
        known_face_encodings.append(face_encodings[0])
        known_face_names.append("Henrique")

    with open('encodings.pkl', 'wb') as f:
        pickle.dump((known_face_encodings, known_face_names), f)

def load_model():
    return pickle.loads(open("embedded/encodings.pkl", "rb").read())

def recognize_customer(recognize_customer_event_flag, customer_queue):
    data = load_model()
    video_capture = cv2.VideoCapture(0)
    
    while True:
        
        face_detection_count = defaultdict(int)
        while recognize_customer_event_flag.is_set():

            ret, frame = video_capture.read()
            frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            print("Looking for someone")

            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            for encoding in face_encodings:
                matches = face_recognition.compare_faces(data["encodings"], encoding)
                customer_id = "Unknown"

                if True in matches:
                    matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                    counts = {}

                    for i in matchedIdxs:
                        customer_id = data["names"][i]
                        counts[customer_id] = counts.get(customer_id, 0) + 1

                    customer_id = max(counts, key=counts.get)
                    face_detection_count[customer_id] += 1
                    print(f"Recognized {customer_id}")

            print(face_detection_count)
            for customer_id, count in face_detection_count.items():
                if count >= 4:
                    customer_queue.put(customer_id)
                    recognize_customer_event_flag.clear()

            time.sleep(1)

        time.sleep(2)