import json
import multiprocessing
from embedded.gpt_dtos.dto import RegisterResponseFormat, ResponseStopFormat
import gpt
import os
from dotenv import load_dotenv
from openai import OpenAI

import base64
import cv2
import time
import numpy as np
import embedded.coffee_api.api as coffee_api

load_dotenv()
API_KEY = os.getenv("API_KEY")
client = OpenAI(api_key=API_KEY)

phase_prompt = [
    {
        "name": "AskToRegisterState",
        "goal": "Figure out if the user wants to register as a customer to this service. If he does, get his firstname and lastname and return them in firstname and lastname vars.",
        "guideline": "Say the customer's order has finished being dispensed. Then, ask if the customer wants to register as a customer to this service.",
    },
    {
        "name": "TakePictureState",
        "goal": "Get the user to stand in front of the camera to take pictures for facial recognition.",
        "guideline": "Ask the customer to stand in front of the camera with a clear view of their face to take pictures. Start a 3 second countdown to take the picture.",
    },
    {
        "name": "Incompatible",
        "goal": "Determine if the user is asking something that is not about his registration process.",
        "guideline": "Say that the machine does not provide what the user wants, the reason why and to try again later.",
    },
]
stop_prompt = [
    {
        "name": "Desinterested",
        "goal": "if the user is not interested in registering to this service.",
        "guideline": "Say goodbye to the customer.",
    },    
]

def generate_response(
    audio_queue: multiprocessing.Queue,
    capture_audio_event_flag,
    register_customer_event_flag
):
    global phase_prompt, stop_prompt
    while True:
        while not register_customer_event_flag.is_set():
            pass
        confirmed_firstname = None
        confirmed_lastname = None
        finished_conversation = False
        history = []
        while not finished_conversation:
            for state in phase_prompt:
                prompt = f"""Verify if the current phase is {state['name']}. The phase's goal is: "{state['goal']}". 
                        Return true in inPhase in case the phase goal has not been accomplished. Return false in case the objective has been accomplished.
                        To reach the goal, you must {state['guideline']}.
                        Call the customer coffee enthusiast.
                        ."""

                in_phase, response, firstname, lastname = request(
                    history, prompt
                )
                if in_phase:
                    print(f"State: {state['name']}")
                    print(f"Goal: {state['goal']}")
                    print(f"Guideline: {state['guideline']}")
                    print(f"Message: {response}")
                    history.append({"role": "system", "content": response})
                    if lastname != '':
                        confirmed_lastname = lastname
                        print(f"Saving lastname {confirmed_lastname}")
                    if firstname != '':
                        confirmed_firstname = firstname
                        print(f"Saving firstname {confirmed_firstname}")

                    if state["name"] == "TakePictureState":
                        finished_conversation = True
                        pics = capture_pictures_base64(3, 2)
                        register_new_customer(confirmed_firstname, confirmed_lastname, pics)
                        gpt.play_audio("Thank you for registering, goodbye!")
                        register_customer_event_flag.clear()
                        break

            gpt.play_audio(response)
            if finished_conversation:
                print(
                    f"Finished register phase conversation."
                )
                break
            try:
                capture_audio_event_flag.set()
                audio_buffer = audio_queue.get(timeout=20)
                print("Got audio from queue")
            except Exception as e:
                print("No response given by the customer, restarting flow")
                capture_audio_event_flag.clear()
                register_customer_event_flag.clear()
                finished_conversation = True
                break

            user_response = gpt.transcript(audio_buffer)
            history.append({"role": "user", "content": user_response})

            for sp in stop_prompt:
                prompt = f"Verify if the current reason to stop is {sp['name']}. To determine if it is, figure out {sp['goal']}. Return true in stop in case the conversation must stop. To determine it, you must {sp['guideline']}., only generate a message if stop is True"
                stop, response, reason = has_to_stop(history, prompt)

                if stop:
                    print(f"State: {sp['name']}")
                    print(f"Goal: {sp['goal']}")
                    print(f"Guideline: {sp['guideline']}")
                    history.append({"role": "system", "content": response})
                    gpt.play_audio(response)
                    register_customer_event_flag.clear()
                    finished_conversation = True
                    break                    


def register_new_customer(firstname: str, lastname: str, pics: list):
    print(f"Registering new customer: {firstname} {lastname}")
    new_customer = coffee_api.add_customer(firstname, lastname)
    for pic in pics:
        coffee_api.add_picture(new_customer["customer"][0]["id"], pic)

def request(
    history: list, phase_prompt: str
) -> tuple:
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
    reason = response["reason"]

    return stop, message, reason

def capture_pictures_base64(picture_count=2, delay=2):
    """
    Capture a specified number of pictures and return them as base64 strings.

    Args:
        picture_count (int): Number of pictures to capture.
        delay (int): Delay in seconds between each picture.

    Returns:
        List[str]: List of base64-encoded strings for each captured picture.
    """
    # Open the video capture
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        raise RuntimeError("Failed to open video capture device.")

    base64_images = []

    try:
        for _ in range(picture_count):
            # Capture a frame
            ret, frame = video_capture.read()
            if not ret:
                print("Failed to capture frame.")
                break

            # Encode the frame to JPEG format
            _, buffer = cv2.imencode('.jpg', frame)

            # Convert the buffer to a base64 string
            base64_image = base64.b64encode(buffer).decode('utf-8')
            base64_images.append(base64_image)

            print("Captured a base64-encoded image.")
            
            # Wait for the specified delay
            time.sleep(delay)
    finally:
        # Release the video capture
        video_capture.release()
        print("Released video capture device.")

    return base64_images

def register_customer(
    audio_queue: multiprocessing.Queue,
    capture_audio_event_flag,
    register_customer_event_flag,
    ):
    generate_response(audio_queue, capture_audio_event_flag, register_customer_event_flag)