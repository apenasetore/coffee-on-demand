import base64
from collections import defaultdict
import time
import cv2
import face_recognition
import pickle
import embedded.gpt_audio_preview as gpt

import numpy as np

from embedded.coffee_api.api import get_customers
from embedded.coffee_api.http_requests import get
from embedded.arduino import send_to_arduino


def process_base64_image(base64_string):
    binary_data = base64.b64decode(base64_string)
    image_array = np.frombuffer(binary_data, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return image


def generate_new_encodings(
    generate_new_encodings_event_flag,
    recognize_customer_event_flag,
    load_encodings_event_flag,
):
    while not generate_new_encodings_event_flag.is_set():
        pass

    customers = get_customers()

    gpt.play_audio(
        "I'm taking a time to generate my new data for recognition of the last customer. One minute please."
    )
    send_to_arduino("UPDATE:STATE:PROCESSING")

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

    gpt.play_audio("Okay, all set, let's go.")

    load_encodings_event_flag.set()
    recognize_customer_event_flag.set()
    generate_new_encodings_event_flag.clear()


def load_model():
    try:
        return pickle.loads(open("embedded/encodings.pkl", "rb").read())
    except Exception as e:
        return {"encodings": [], "names": []}


def recognize_customer(
    recognize_customer_event_flag,
    load_encodings_event_flag,
    register_customer_event_flag,
    customer_queue,
    camera_event_flag,
    frames_queue,
):
    data = load_model()
    while True:
        displayed_info = False
        face_detection_count = defaultdict(int)
        
        while not recognize_customer_event_flag.is_set():
            pass

        if not displayed_info:
            displayed_info = True
            send_to_arduino("UPDATE:STATE:IDLE")

        if load_encodings_event_flag.is_set():
            data = load_model()
            load_encodings_event_flag.clear()

        camera_event_flag.set()
        frame = frames_queue.get()

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

        if face_locations and customer_id == -1:
            face_detection_count[customer_id] += 1
            print(f"Recognized {customer_id}")

        print(face_detection_count)
        for customer_id, count in face_detection_count.items():
            if count >= 1:
                customer_queue.put(customer_id)
                gpt.play_audio("Oh, hi there!")
                # register_customer_event_flag.set()
                recognize_customer_event_flag.clear()
                camera_event_flag.clear()
                break

        time.sleep(0.3)

        time.sleep(2)
