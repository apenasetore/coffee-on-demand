import json
import multiprocessing
from embedded.gpt_dtos.dto import RegisterResponseFormat, ResponseStopFormat
import embedded.gpt as gpt
import os
from dotenv import load_dotenv
from openai import OpenAI

import base64
import cv2
import time
import numpy as np
import embedded.coffee_api.api as coffee_api
from embedded.arduino import send_to_arduino
from embedded.client_recognition import video_capture

load_dotenv()
API_KEY = os.getenv("API_KEY")
client = OpenAI(api_key=API_KEY)

phase_prompt = [
    {
        "name": "AskToRegisterState",
        "phase_identification": "Customer has given no information about his first and last name yet.",
        "goal": "Figure out if the user wants to register as a customer to this service. If he does, get his firstname and lastname and return them in firstname and lastname vars, else return empty string",
        "guideline": "Say the customer's order has finished being dispensed. Then, ask if the customer wants to register as a customer to this service.",
    },
    {
        "name": "TakePictureState",
        "phase_identification": "Customer has already given his first and last name.",
        "goal": "Get the user to stand in front of the camera to take pictures for facial recognition. If you have the customer name, you are in this state.",
        "guideline": "Ask the customer to stand in front of the camera with a clear view of their face to take pictures. Start a 3 second countdown to take the picture.",
    },
    {
        "name": "Incompatible",
        "phase_identification": "Customer has said some something that is not about his registration process",
        "goal": "Determine if the user is asking something that is not about his registration process.",
        "guideline": "Say that the machine does not provide what the user wants, the reason why and to try again later.",
    },
]
stop_prompt = [
    {
        "name": "Desinterested",
        "goal": "if the user is not interested in registering to this service.",
        "guideline": "Say goodbye to the customer.",
        "phase_identification": "Customer has explicitly said he is not interested in registering.",
    },
]


def generate_response(
    audio_queue: multiprocessing.Queue,
    purchase_queue: multiprocessing.Queue,
    capture_audio_event_flag,
    register_customer_event_flag,
    recognize_customer_event_flag,
    generate_new_encodings_event_flag,
):
    global phase_prompt, stop_prompt
    while True:
        while not register_customer_event_flag.is_set():
            pass

        purchase = purchase_queue.get()
        weight = purchase["weight"]
        coffee_id = purchase["coffee_id"]

        confirmed_firstname = None
        confirmed_lastname = None
        finished_conversation = False
        history = []
        while not finished_conversation:
            for state in phase_prompt:
                prompt = f"""Verify if the current phase is {state['name']}.
                        To indentify if you are in this state use this information: {state["phase_identification"]}.
                        The phase's goal is: "{state['goal']}". 
                        Return true in in_phase in case the phase goal has not been accomplished. Return false in case the objective has been accomplished.
                        To reach the goal, you must {state['guideline']}.
                        Call the customer coffee enthusiast.
                        ."""

                in_phase, response, firstname, lastname = request(history, prompt)
                if in_phase:
                    print(f"State: {state['name']}")
                    print(f"Goal: {state['goal']}")
                    print(f"Guideline: {state['guideline']}")
                    print(f"Message: {response}")
                    history.append({"role": "system", "content": response})
                    if lastname != "":
                        confirmed_lastname = lastname
                        print(f"Saving lastname {confirmed_lastname}")
                    if firstname != "":
                        confirmed_firstname = firstname
                        print(f"Saving firstname {confirmed_firstname}")

                    if state["name"] == "TakePictureState":
                        gpt.play_audio(response)
                        finished_conversation = True
                        send_to_arduino("UPDATE:STATE:REGISTERING")
                        pics = capture_pictures_base64(3, 2)
                        gpt.play_audio(
                            "I've already taken your pictures, now I will send them to registration! Thank you for your purchase."
                        )
                        new_id = register_new_customer(
                            confirmed_firstname, confirmed_lastname, pics
                        )
                        coffee_api.add_purchase(new_id, weight, coffee_id)

                        register_customer_event_flag.clear()
                        generate_new_encodings_event_flag.set()
                        print(f"Finished register phase conversation.")

                    break

            if finished_conversation:
                break

            gpt.play_audio(response)
            try:
                capture_audio_event_flag.set()
                send_to_arduino("UPDATE:STATE:LISTENING")
                audio_buffer = audio_queue.get(timeout=20)
                print("Got audio from queue")
                send_to_arduino("UPDATE:STATE:PROCESSING")
            except Exception as e:
                print("No response given by the customer, restarting flow")
                coffee_api.update_coffee_quantity(coffee_id, weight)
                capture_audio_event_flag.clear()
                register_customer_event_flag.clear()
                recognize_customer_event_flag.set()
                finished_conversation = True
                break

            user_response = gpt.transcript(audio_buffer)
            history.append({"role": "user", "content": user_response})

            for sp in stop_prompt:
                prompt = f"Verify if the current reason to stop is {sp['name']}. To determine if it is, figure out {sp['goal']}. Return true in stop in case the conversation must stop. To determine it, you must {sp['guideline']}., only generate a message if stop is True"
                stop, response = has_to_stop(history, prompt)

                if stop:
                    print(f"State: {sp['name']}")
                    print(f"Goal: {sp['goal']}")
                    print(f"Guideline: {sp['guideline']}")
                    print(f"Message: {response}")
                    history.append({"role": "system", "content": response})
                    gpt.play_audio(response)
                    coffee_api.update_coffee_quantity(coffee_id, weight)
                    register_customer_event_flag.clear()
                    recognize_customer_event_flag.set()
                    finished_conversation = True
                    break


def register_new_customer(firstname: str, lastname: str, pics: list):
    print(f"Registering new customer: {firstname} {lastname}")
    new_customer = coffee_api.add_customer(firstname, lastname)
    for pic in pics:
        coffee_api.add_picture(new_customer["customer"][0]["id"], pic)

    return new_customer["customer"][0]["id"]


def request(history: list, phase_prompt: str) -> tuple:
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""
                You are a coffee vending machine in a registration phase that aims to register new customers. 
                You provide only coffee grains and can register users with their consent.
                Respond to this text according to the phase instructions. 
                {phase_prompt}.
                Continue this convesation with the user.
                """,
            }
        ]
        + (history if len(history) else []),
        response_format=RegisterResponseFormat,
    )
    response = json.loads(response.choices[0].message.content)

    in_phase = response["in_phase"]
    message = response["message"]
    firstname = response["firstname"]
    lastname = response["lastname"]

    return in_phase, message, firstname, lastname


def has_to_stop(history: list, phase_prompt: str) -> tuple:
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""
                    You are a coffee vending machine in a registration phase that aims to register new customers. 
                    You provide only coffee grains and can register users with their consent.  
                    Respond to this text according to the phase instructions: 
                    {phase_prompt}.  
                    Continue this conversation with the user.
                    """,
            }
        ]
        + (history if len(history) else []),
        response_format=ResponseStopFormat,
    )
    response = json.loads(response.choices[0].message.content)
    stop = response["stop"]
    message = response["message"]

    return stop, message


def capture_pictures_base64(picture_count, delay):

    time.sleep(0.3)
    base64_images = []

    try:
        for i in range(picture_count):
            # Capture a frame
            ret, frame = video_capture.read()
            if not ret:
                print("Failed to capture frame.")
                break

            _, buffer = cv2.imencode(".jpg", frame)

            base64_image = base64.b64encode(buffer).decode("utf-8")
            base64_images.append(base64_image)

            print("Captured a base64-encoded image.")

            time.sleep(delay)
    except Exception as e:
        print(f"Error taking pictures: {e}")
        gpt.play_audio(
            "Oh, some error occurred during the pictures. So we cant't procceed. Anyway, thank you for your purchase!"
        )

    return base64_images


def register_customer(
    audio_queue: multiprocessing.Queue,
    purchase_queue: multiprocessing.Queue,
    capture_audio_event_flag,
    register_customer_event_flag,
    recognize_customer_event_flag,
    generate_new_encodings_event_flag,
):
    generate_response(
        audio_queue,
        purchase_queue,
        capture_audio_event_flag,
        register_customer_event_flag,
        recognize_customer_event_flag,
        generate_new_encodings_event_flag,
    )
