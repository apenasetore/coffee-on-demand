import asyncio
import json
import multiprocessing
from embedded.gpt_dtos.dto import GPTInteractionRegistration
import embedded.gpt_henrique as gpt
import os
from dotenv import load_dotenv
import openai

import base64
import cv2
import time
import numpy as np
import embedded.coffee_api.api as coffee_api
from embedded.arduino import send_to_arduino

load_dotenv()
API_KEY = os.getenv("API_KEY")
client = openai.AsyncOpenAI(api_key=API_KEY)


async def generate_response(
    audio_queue: multiprocessing.Queue,
    purchase_queue: multiprocessing.Queue,
    capture_audio_event_flag,
    register_customer_event_flag,
    recognize_customer_event_flag,
    generate_new_encodings_event_flag,
    camera_event_flag,
    frames_queue,
):
    phases = [
        {
            "name": "AskToRegisterState",
            "goal": "Figure out if the user wants to register as a customer to this service. If he does, get his firstname and lastname and return them in firstname and lastname vars, else return empty string",
            "guideline": "Say the customer's order has finished being dispensed. Then, ask if the customer wants to register as a customer to this service. Ask if the costumer wants to go BC",
        },
        {
            "name": "TakePictureState",
            "goal": "Get the user to stand in front of the camera to take pictures for facial recognition. If you have the customer name, you are in this state.",
            "guideline": "Ask the customer to stand in front of the camera with a clear view of their face to take pictures. Start a 3 second countdown to take the picture. Do no use emojis",
        },
        {
            "name": "Incompatible",
            "goal": "Politely redirect the user back to registration topics if the conversation strays.",
            "guideline": "If the user discusses unrelated topics, gently bring the conversation back to the main topic",
        },
    ]
    while True:

        purchase = purchase_queue.get()
        weight = purchase["weight"]
        coffee_id = purchase["coffee_id"]

        main_prompt = f"""You are a coffee vending machine that sells coffee grains. Follow the instructions below:
                - Your task is to analyze the conversation history and determine if the client wants to register on the machine.
                - Answer in an extremely concise way, with very short text, without topics.
                - Benefits of registration are: be recognized when arrive again in the machine, receive recommendations based on previous purchases.
                - Conversation phases: {phases}
                """

        conversation_history = []
        register = False
        while True:

            start = time.perf_counter()
            gpt_response = await request(main_prompt, conversation_history)
            print(f"Time checking main phases {time.perf_counter() - start}s")
            print(gpt_response)

            conversation_history.append(
                {"role": "assistant", "content": gpt_response.response}
            )

            gpt.play_audio(gpt_response.response)
            if gpt_response.completed_conversation:
                register = (
                    True if gpt_response.firstname and gpt_response.lastname else False
                )
                break

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
                break

            user_response = await gpt.transcript(audio_buffer)
            conversation_history.append({"role": "user", "content": user_response})

        if register:
            send_to_arduino("UPDATE:STATE:REGISTERING")
            gpt.play_audio("Please look at the camera while I take your pictures in 3, 2, 1, look at the little bird")
            pics = capture_pictures_base64(3, 2, camera_event_flag, frames_queue)
            gpt.play_audio(
                "I've already taken your pictures, now I will send them to registration! Thank you for your purchase."
            )
            new_id = register_new_customer(
                gpt_response.firstname, gpt_response.lastname, pics
            )
            coffee_api.add_purchase(new_id, weight, coffee_id)

            register_customer_event_flag.clear()
            generate_new_encodings_event_flag.set()
            print(f"Finished register phase conversation.")


def register_new_customer(firstname: str, lastname: str, pics: list):
    print(f"Registering new customer: {firstname} {lastname}")
    new_customer = coffee_api.add_customer(firstname, lastname)
    for pic in pics:
        coffee_api.add_picture(new_customer["customer"][0]["id"], pic)

    return new_customer["customer"][0]["id"]


async def request(system_prompt: str, conversation_history: list[dict]):
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    response = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=messages,
        response_format=GPTInteractionRegistration,
    )
    response = json.loads(response.choices[0].message.content)

    return GPTInteractionRegistration(**response)


def capture_pictures_base64(picture_count, delay, camera_event_flag, frames_queue):
    base64_images = []

    try:
        for i in range(picture_count):
            # Capture a frame
            camera_event_flag.set()
            frame = frames_queue.get()
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
    camera_event_flag,
    frames_queue,
):
    asyncio.run(
        generate_response(
            audio_queue,
            purchase_queue,
            capture_audio_event_flag,
            register_customer_event_flag,
            recognize_customer_event_flag,
            generate_new_encodings_event_flag,
            camera_event_flag,
            frames_queue,
        )
    )
