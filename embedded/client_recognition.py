import base64
from collections import defaultdict
import time
import cv2
import face_recognition
import os
import pickle

import numpy as np

from embedded.coffee_api.api import get_customers
from embedded.coffee_api.http_requests import get


def process_base64_image(base64_string):
    binary_data = base64.b64decode(base64_string)
    image_array = np.frombuffer(binary_data, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return image


def generate_new_encodings(generate_new_encodings_event_flag):
    customers = get_customers()

    known_face_encodings = []
    known_face_names = []
    for customer_info in customers:
        pictures = customer_info["pictures"]
        customer_id = customer_info["customer"]["id"]
        for picture in pictures:
            picture_url = picture["picture_url"]
            response = get(url=picture_url)
            image_array = np.frombuffer(response.content, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(image, model="hog")
            encodings = face_recognition.face_encodings(image, boxes)

            for encoding in encodings:
                known_face_encodings.append(encoding)
                known_face_names.append(customer_id)

    data = {"encodings": known_face_encodings, "names": known_face_names}
    with open("embedded/encodings.pkl", "wb") as f:
        pickle.dump(data, f)


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
                customer_id = -1

                if True in matches:
                    matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                    counts = {}

                    for i in matchedIdxs:
                        customer_id = data["names"][i]
                        counts[customer_id] = counts.get(customer_id, 0) + 1

                    customer_id = max(counts, key=counts.get)
                    face_detection_count[customer_id] += 1
                    print(f"Recognized {customer_id}")

            if face_locations:
                face_detection_count[customer_id] += 1
                print(f"Recognized {customer_id}")

            print(face_detection_count)
            for customer_id, count in face_detection_count.items():
                if count >= 4:
                    customer_queue.put(customer_id)
                    recognize_customer_event_flag.clear()

            time.sleep(1)

        time.sleep(2)
