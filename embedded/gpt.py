import io
import json
import multiprocessing
import os
import time
import tempfile
import concurrent.futures

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
            "goal": "Welcome the user and understand their needs.",
            "guideline": "Greet the user warmly. If their name is known, address them personally. Ask how you can assist.",
            "phase_identification": "The user has not started discussing coffee preferences yet."
        },
        {
            "name": "AvailableCoffeeState",
            "goal": "Help the user choose a coffee based on preferences.",
            "guideline": "Ask the user which coffee they prefer. Provide descriptions only if requested. If the user is registered, suggest coffees based on their purchase history.",
            "phase_identification": "The user is discussing coffee options."
        },
        {
            "name": "QuantityState",
            "goal": "Determine the desired coffee quantity within the allowed range.",
            "guideline": "Ask how many grams the user wants (20-300g). Verify the stock availability. If the quantity is invalid or exceeds stock, explain and re-prompt.",
            "phase_identification": "The user is deciding on the coffee quantity."
        },
        {
            "name": "OrderConfirmationState",
            "goal": "Confirm the user's order and prepare for payment.",
            "guideline": "Summarize the order, including coffee type, quantity, and total price. Ask for confirmation to proceed.",
            "phase_identification": "The user has finalized coffee and quantity selection."
        },
        {
            "name": "GoodbyeState",
            "goal": "Conclude the interaction politely.",
            "guideline": "Thank the user and say goodbye. Ask no more questions.",
            "phase_identification": "The user has confirmed their order.",
        },
        {
        "name": "Incompatible",
        "goal": "Redirect the conversation to coffee or coffee bean topics when the user introduces unrelated subjects.",
        "guideline": "If the user asks about something unrelated to coffee, politely redirect the conversation by highlighting coffee options or services. Example: 'I specialize in helping with coffee selections and orders. Could I interest you in exploring our coffee options?'",
        "phase_identification": "You are in this phase when the user asks about topics unrelated to the machine's capabilities or offerings. This phase does not apply if the user is discussing coffee-related topics but shows disinterest in continuing."
    }

    ]

    stop_prompt = [
           {
        "name": "Disinterested",
        "goal": "the user explicitly said he is no longer interested in the buying process.",
        "guideline": "The user must say explicitly that he is not interest in anything coffee related."
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
                prompt = f"""
                            Verify if the current phase is {state['name']}. 
                            Use the following criteria: Phase identification: {state["phase_identification"]}. Phase goal: {state['goal']}.
                            Return `inPhase = True` if the goal is not yet achieved, and `inPhase = False` otherwise. 
                            To accomplish the goal follow these guidelines: {state["guideline"]}.
                            Additional details: Client's name: {name}. Purchase history: {json.dumps(purchase_history) if purchase_history else 'None'}. Coffee price: Per gram (calculate the total price).
                            Be concise in responses and focus on achieving the goal efficiently.
                        """

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

            if in_phase:
                play_audio(response)

            if finished_conversation:
                print(
                    f"Finished conversation, generating pix and waiting for deposit."
                )

                pix = create_payment(total)
                print(pix)
                # send_to_arduino(pix["payload"]["payload"])
                play_audio("Please scan the QR Code in the LCD screen to pay.")
                print(pix["paymentId"])
                payment = verify_payment(pix["paymentId"])
                while not payment["paid"]:
                    print(payment["paid"])
                    payment = verify_payment(pix["paymentId"])
                    time.sleep(3)

                chosen_coffee = None
                for coffee in coffees:
                    if coffee["container"] == str(confirmed_container):
                        chosen_coffee = coffee
                        break

                print(
                    f"Finished conversation, putting order of container {confirmed_container}, {confirmed_quantity} grams."
                )

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
                
                prompt = f"""Verify if the current reason to stop is '{sp["name"]}'.
                            Return true if {sp["goal"]}, otherwise return `False`.
                            To make this determination, {sp["guideline"]}.
                            Only generate a response if 'stop = True'.
                            """
                stop, response = has_to_stop(coffees, history, prompt)
                print(stop)
                if stop:
                    print(f"State: {sp['name']}")
                    print(f"Goal: {sp['goal']}")
                    print(f"Guideline: {sp['guideline']}")
                    history.append({"role": "system", "content": response})
                    play_audio(response)
                    if sp["name"] == 'Disinterested':
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






def has_to_stop(coffees: list, history: list, prompt: str) -> tuple:
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""You are a coffee vending machine with these coffee grains available: {json.dumps(coffees)}. 
                    You provide only coffee grains and can register users with their consent.  
                    {prompt}.
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
            model="whisper-1", file=file, language="en",
            prompt="Reais, Etore, Henrique, Maria Luiza, Francisco, Felipe, Heitor"
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
