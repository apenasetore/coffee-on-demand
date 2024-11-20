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

    with open('modelo_reconhecimento.pkl', 'wb') as f:
        pickle.dump((known_face_encodings, known_face_names), f)

def load_model():
    return pickle.load("encodings.pkl", "rb")

def recognize_customer():
    data = load_model()
    video_capture = cv2.VideoCapture(0)
    
    while True:
        ret, frame = video_capture.read()
        frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        for encoding in face_encodings:
            matches = face_recognition.compare_faces(data["encodings"], encoding)
            name = "Unknown"

            if True in matches:
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}

                for i in matchedIdxs:
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1

                name = max(counts, key=counts.get)