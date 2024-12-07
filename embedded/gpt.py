import io
import json
import multiprocessing
import os
import time
import tempfile
from dotenv import load_dotenv
from gtts import gTTS
import wave
from embedded.gpt_dtos.dto import ResponseFormat, ResponseStopFormat
import pygame
from pydub import AudioSegment
from openai import OpenAI

from embedded.audio import CHANNELS, RATE
from embedded.coffee_api.api import get_purchases, get_coffees, create_payment, verify_payment
from embedded.arduino import send_to_arduino

load_dotenv()
API_KEY = os.getenv("API_KEY")
client = OpenAI(api_key=API_KEY)


def generate_response(
    customer_queue: multiprocessing.Queue,
    audio_queue: multiprocessing.Queue,
    measure_coffee_queue: multiprocessing.Queue,
    capture_audio_event_flag,
    recognize_customer_event_flag,
):
    phase_prompt = [
        {
            "name": "IntroductionState",
            "goal": "Present to the user and ask how you can help.",
            "guideline": "Say hello and welcome the guest to the machine. Keep the conversation natural. Call them by their name, if in client mode.",
        },
        {
            "name": "AvailableCoffeeState",
            "goal": "Figure out what is the user's coffee of interest.",
            "guideline": "Talk to the user about which of the available coffees suits their taste. Use the coffee description ONLY if the customer asks form more information. You can use customer's purchase history, if known, to try to make suggestions of coffees to buy.",
        },
        {
            "name": "QuantityState",
            "goal": "Get how much of the coffee the consumer wants, considering the bounds.",
            "guideline": "Ask about the quantity of grams the user wants. The limit is from 20 to 300 grams. Do not allow the user to get out of those bounds. Also, use coffee information to see how much coffee is in stock through the stock_grams field. Do not let the user order more than the amount in stock. If user selects invalid quantity, ask again",
        },
        {
            "name": "OrderConfirmationState",
            "goal": "Get confirmation from the user about the order and payment.",
            "guideline": "Confirm the order with the user by repeating it for them. Tell the price and ask for confirmation. Returns in quantity the amount of coffee the user required",
        },
        {
            "name": "GoodbyeState",
            "goal": "Finish order and say goodbye.",
            "guideline": "Say goodbye to the customer.",
        },
    ]
    stop_prompt = [
        {
            "name": "Desinterested",
            "goal": "The user is not interested in buying coffee anymore.",
            "guideline": "Say goodbye to the customer.",
        },
        {
            "name": "Incompatible",
            "goal": "The user asks something not coffee or coffee beans related",
            "guideline": "Say goodbye to the customer.",
        },
    ]

    while True:
        customer = customer_queue.get()
        finished_conversation = False
        print(f"GPT task received info that customer {customer} arrived")
        purchases = get_purchases(customer)
        customer_info = purchases.get("customer")
        purchase_history = purchases.get("purchases")
        coffees = get_coffees(only_active=True)
        name = customer_info.get("firstname") if customer_info else "coffee enthusiast"
        history = []
        confirmed_quantity = 0
        confirmed_container = 0
        while not finished_conversation:
            for state in phase_prompt:
                prompt = f"""Verify if the current phase is {state['name']}. The phase's goal is {state['goal']}. 
                        Return true in inPhase in case the phase goal has not been accomplished. Return false in case the objective has been accomplished. 
                        To reach the goal, you must {state['guideline']}. 
                        Client's name is {name}. This client is {"not" if name == "coffee enthusiast" else ""} registered and his purchase history is {json.dumps(purchase_history) if purchase_history else '[]'}.
                        When asked, you can use the purchase history to suggest coffees to the client based on previous purchases and customer's tastes.
                        The price of each coffee is price per 1 gram, so you need to do the math to tell the total price.
                        If client is not registered and wants to register in the RegisterState, return True in want_to_register, else return False. The RegisterState can be skipped if client is registered and proceed to GoodbyeState
                        Be objective in responses, with minimum words."""

                in_phase, response, quantity, container, total = request(
                    coffees, history, prompt, None
                )
                if in_phase:
                    print(f"State: {state['name']}")
                    print(f"Goal: {state['goal']}")
                    print(f"Guideline: {state['guideline']}")
                    print(f"Response: {response}")
                    history.append({"role": "system", "content": response})
                    if quantity != 0:
                        confirmed_quantity = quantity
                        print(f"Saving quantity of {confirmed_quantity} grams")
                    if container != 0:
                        confirmed_container = container
                        print(f"Saving container number {confirmed_container}")

                    if state["name"] == "GoodbyeState":
                        finished_conversation = True

                    break

            play_audio(response)
            if finished_conversation:
                print(
                    f"Finished conversation, putting order of {confirmed_quantity} in to dispense queue"
                )

                # pix = create_payment(total)
                # print(pix)
                # send_to_arduino(pix["payload"]["payload"])
                # play_audio("Please scan the QR Code in the LCD screen to pay.")
                # print(pix["payment_id"])
                # payment = verify_payment(pix["payment_id"])
                # while not payment["received"]:
                #     payment = verify_payment(pix["payment_id"])
                #     time.sleep(3)

                chosen_coffee = None
                for coffee in coffees:
                    if coffee["container"] == str(confirmed_container):
                        chosen_coffee = coffee
                        break

                measure_coffee_queue.put(
                    {"container_id": confirmed_container - 1, "weight": confirmed_quantity, "customer_id": customer, "coffee_id": chosen_coffee}
                )

                break
            try:
                capture_audio_event_flag.set()
                audio_buffer = audio_queue.get(timeout=20)
                print("Got audio from queue")
            except Exception as e:
                print("No response given by the customer, restarting flow")
                capture_audio_event_flag.clear()
                recognize_customer_event_flag.set()
                break

            user_response = transcript(audio_buffer)
            history.append({"role": "user", "content": user_response})

            for sp in stop_prompt:
                prompt = f"Verify if the current reason to stop is {sp['name']}. To determine that {sp['goal']}. Return true in stop in case the conversation must stop. To determine it, you must {sp['guideline']}., only generate a message if stop is True"
                stop, response, reason = has_to_stop(coffees, history, prompt)

                if stop:
                    print(f"State: {sp['name']}")
                    print(f"Goal: {sp['goal']}")
                    print(f"Guideline: {sp['guideline']}")
                    history.append({"role": "system", "content": response})
                    play_audio(response)
                    finished_conversation = True
                    recognize_customer_event_flag.set()
                    break


def request(
    coffees: list, history: list, phase_prompt: str, purchase_history: list
) -> tuple:
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""You are a coffee vending machine with these coffee grains available: {json.dumps(coffees)}.  
                You are selling in Reais, Brazil's currency. Do not speak portuguese.
                Respond to this text according to the phase instructions. Answer in a text-to-speech friendly way, never use topics.
                {phase_prompt}.
                Continue this convesation with the user.
                The user's purchase history is {json.dumps(purchase_history) if purchase_history else "[]"}
                """,
            }
        ]
        + (history if len(history) else []),
        response_format=ResponseFormat,
    )
    response = json.loads(response.choices[0].message.content)

    in_phase = response["in_phase"]
    message = response["message"]
    quantity = response["quantity"]
    container = response["container"]
    total = response["total"]

    return in_phase, message, quantity, container, total


def has_to_stop(coffees: list, history: list, phase_prompt: str) -> tuple:
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""You are a coffee vending machine with these coffee grains available: {json.dumps(coffees)}. 
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


def transcript(audio: list) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        with wave.open(temp_audio_file, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b"".join(audio))

        temp_audio_file.seek(0)
        file = io.BufferedReader(open(temp_audio_file.name, "rb"))

        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=file, language="en"
        )
        user_response = transcript.text

    print(f"User said: {user_response}")
    return user_response


def play_audio(text: str):
    print("Text to speech...")
    audio = gTTS(text=text, lang="en", slow=False)
    print("Completed transformation")
    pygame.mixer.init()
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as temp_audio:
        audio.save(temp_audio.name)

        pygame.mixer.music.load(temp_audio.name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.3)

    print("Finished playing sound")
