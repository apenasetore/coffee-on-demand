import base64
import io
import json
import multiprocessing
import os
import time
import tempfile
from dotenv import load_dotenv
import time
import wave
from embedded.gpt_dtos.dto import GPTAudioResponse, GPTDataResponse, GPTInteraction
import openai
import time
import pygame

from embedded.audio import CHANNELS, RATE
from embedded.coffee_api.api import (
    get_purchases,
    get_coffees,
    create_payment,
    verify_payment,
)
from embedded.arduino import send_to_arduino

load_dotenv()
API_KEY = os.getenv("API_KEY")
client = openai.OpenAI(api_key=API_KEY)


def generate_response(
    customer_queue: multiprocessing.Queue,
    audio_queue: multiprocessing.Queue,
    measure_coffee_queue: multiprocessing.Queue,
    capture_audio_event_flag,
    recognize_customer_event_flag,
):

    execute(
        customer_queue,
        audio_queue,
        measure_coffee_queue,
        capture_audio_event_flag,
        recognize_customer_event_flag,
    )


def execute(
    customer_queue: multiprocessing.Queue,
    audio_queue: multiprocessing.Queue,
    measure_coffee_queue: multiprocessing.Queue,
    capture_audio_event_flag,
    recognize_customer_event_flag,
):
    phases = [
        {
            "name": "IntroductionState",
            "goal": "Greet the user warmly and understand their initial needs.",
            "guideline": "Welcome the user with a friendly greeting. If their name is known, address them personally (e.g., 'Hello, [name]!'). Ask how you can assist with their coffee selection or purchase. Do not make topics, be concise",
        },
        {
            "name": "AvailableCoffeeState",
            "goal": "Provide information about the available coffee options and help the user make a choice.",
            "guideline": "Ask the user which coffee type they prefer. If requested, provide descriptions of the available options. If the user is registered, suggest coffee options based on their purchase history. Ensure your suggestions are clear and concise. Do not make topics, be concise",
        },
        {
            "name": "QuantityState",
            "goal": "Determine how much coffee the user wants to purchase.",
            "guideline": "Ask the user to specify the quantity of coffee they would like, within the range of 20 to 300 grams. Verify stock availability and provide feedback if the desired quantity exceeds the available stock. If necessary, suggest alternative quantities.Do not make topics, be concise",
        },
        {
            "name": "OrderConfirmationState",
            "goal": "Confirm the user's coffee selection and proceed to the finished phase.",
            "guideline": "Summarize the user's order, including the chosen coffee type, quantity, and total price. Ask for confirmation to proceed with the order and explain the next steps, such as generating a payment QR code.Do not make topics, be concise",
        },
        {
            "name": "FinishedState",
            "goal": "You have not said goodbye to the user after the order confirmation",
            "guideline": "Once the user confirms the order, provide a final thank you message and conclude the conversation without any additional prompts or questions. Ensure that this state marks the complete fulfillment of the order process by returning `inPhase = False` to indicate that the goal is fully achieved.",
        },
        {
            "name": "Incompatible",
            "goal": "Politely redirect the user back to coffee-related topics if the conversation strays.",
            "guideline": "If the user discusses unrelated topics, gently bring the conversation back to coffee options or services. Example: 'I specialize in coffee selections and purchases. Would you like to explore our coffee varieties?'",
        },
    ]

    while True:
        customer = customer_queue.get()
        print(f"GPT task received info that customer {customer} arrived")

        start = time.perf_counter()

        purchases = get_purchases(customer)
        customer_info = purchases.get("customer")
        purchase_history = purchases.get("purchases")
        coffees = get_coffees(only_active=True)

        print(f"Time fetching CoffeeAPI info {time.perf_counter() - start}s")

        name = customer_info.get("firstname") if customer_info else "coffee enthusiast"

        first_stage_prompt = f"""You are a coffee vending machine that sells coffee grains. For the response, always generate audio. 
            Follow the instructions below:  
            - You are selling in Reais, Brazil's currency. Do not speak portuguese.
            - Coffee price is calculated per gram (provide the total price).
            - Coffees available: {json.dumps(coffees)}
            - Your task is to analyze the conversation history and identify in what phase it is
            - Phases of conversation: {phases}
            - Answer in an concise way, very small text, without topics and DO NOT MENTION the phases in response.
            
            Additional details:
            - Client's name: {name}
            - Purchase history: {json.dumps(purchase_history) if purchase_history else 'This client has no purchase history'}."""

        second_stage_prompt = f"""You are a conversation analyzer of a coffee vending machine and a customer.
            You need to read the conversation check if all necessary information has been gotten.
            
            - In this object, you can find in which container is each coffee: {json.dumps(coffees)}
            
            Remember to fill obrigatory fields:
            
            - chosen_coffee_weight
            - container_number (is the number of the container where the chosen coffee is located at)
            - total_price
            - order_confirmed (if and only if the client confirm its order. Do not set it as true if assistant ask and the client didnt answer)"""

        conversation_history = []
        text_conversation_history = []
        proceed_to_payment = False
        while True:

            start = time.perf_counter()
            print(conversation_history)
            gpt_audio_response = generate_audio_response(
                first_stage_prompt, conversation_history
            )
            print(f"Time generating audio response {time.perf_counter() - start}s")
            print(f"Audio transcription: {gpt_audio_response.transcription}")

            conversation_history.append(
                {"role": "assistant", "audio": {"id": gpt_audio_response.audio_id}}
            )
            text_conversation_history.append(
                {"role": "assistant", "content": gpt_audio_response.transcription}
            )

            gpt_data_response = generate_data_from_audio(
                second_stage_prompt, text_conversation_history
            )
            print(f"Time generating data response {time.perf_counter() - start}s")
            print(f"Current data from conversation: {gpt_data_response}")

            play_audio_from_base64(gpt_audio_response.audio_base64)
            if gpt_data_response.order_confirmed:
                proceed_to_payment = True
                break

            try:
                capture_audio_event_flag.set()
                send_to_arduino("UPDATE:STATE:LISTENING")
                audio_buffer = audio_queue.get(timeout=60)
                print("Got audio from queue")
                send_to_arduino("UPDATE:STATE:PROCESSING")
            except Exception as e:
                print("No response given by the customer, restarting flow")
                capture_audio_event_flag.clear()
                play_audio("Oh, I think you are not here anymore. Let's move on.")
                recognize_customer_event_flag.set()
                break

            user_response = transcript(audio_buffer)
            conversation_history.append({"role": "user", "content": user_response})
            text_conversation_history.append({"role": "user", "content": user_response})

        if proceed_to_payment:
            print(f"Finished conversation, generating pix and waiting for deposit.")
            pix = create_payment(gpt_data_response.total_price)
            play_audio("Please scan the QR Code in the LCD screen to pay.")
            send_to_arduino(f"UPDATE:PIX:{pix['payload']['payload']}")
            payment = verify_payment(pix["paymentId"])
            while not payment["paid"]:
                print(payment["paid"])
                payment = verify_payment(pix["paymentId"])
                time.sleep(3)

            chosen_coffee = None
            for coffee in coffees:
                if coffee["container"] == str(gpt_data_response.container_number):
                    chosen_coffee = coffee["id"]
                    break

            print(
                f"Finished conversation, putting order of container {gpt_data_response.container_number}, {gpt_data_response.chosen_coffee_weight} grams."
            )

            play_audio("Payment confirmed! Let's dispense!")

            measure_coffee_queue.put(
                {
                    "container_id": gpt_data_response.container_number - 1,
                    "weight": gpt_data_response.chosen_coffee_weight,
                    "customer_id": customer,
                    "coffee_id": chosen_coffee,
                }
            )


def generate_audio_response(
    system_prompt: str, conversation_history: list[dict]
) -> GPTAudioResponse:
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    gpt_audio_response = client.chat.completions.create(
        model="gpt-4o-mini-audio-preview",
        messages=messages,
        modalities=["text", "audio"],
        audio={
            "voice": "sage",
            "format": "mp3",
        },
        timeout=10,
    )

    audio_id = gpt_audio_response.choices[0].message.audio.id
    audio_base64 = gpt_audio_response.choices[0].message.audio.data
    transcription = gpt_audio_response.choices[0].message.audio.transcript
    return GPTAudioResponse(
        audio_base64=audio_base64,
        transcription=transcription,
        audio_id=audio_id,
    )


def generate_data_from_audio(
    system_prompt: str, conversation_history: list[dict]
) -> GPTDataResponse:
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"The conversation is this: {conversation_history}",
        },
    ]
    gpt_response = client.beta.chat.completions.parse(
        model="gpt-4o-mini", messages=messages, response_format=GPTDataResponse
    )

    gpt_data_response = json.loads(gpt_response.choices[0].message.content)
    return GPTDataResponse(**gpt_data_response)


def transcript(audio: list) -> str:
    start = time.perf_counter()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        with wave.open(temp_audio_file, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b"".join(audio))

        temp_audio_file.seek(0)
        file = io.BufferedReader(open(temp_audio_file.name, "rb"))
        print(
            f"Time to generate audio file to send to whisper = {time.perf_counter() - start}s"
        )
        start = time.perf_counter()
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=file,
            language="en",
            prompt="Reais, Etore, Henrique, Maria Luiza, Francisco, Felipe, Heitor, João, Fabro, Alberto",
        )
        user_response = transcript.text
        print(f"Time to transcript in whisper = {time.perf_counter() - start}s")

    print(f"User said: {user_response}")
    return user_response


def play_audio_from_base64(audio_base64: str):
    start = time.perf_counter()

    audio_bytes = base64.b64decode(audio_base64)
    audio_buffer = io.BytesIO(audio_bytes)

    print(f"Time waiting for base64 decode {time.perf_counter() - start}s")

    start = time.perf_counter()

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    pygame.mixer.music.load(audio_buffer, "mp3")
    pygame.mixer.music.play()

    print(f"Time waiting for pyaudio {time.perf_counter() - start}s")

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


def play_audio(text: str):

    start = time.perf_counter()

    prompt = """Act like a TTS model. You need just to repeat the EXACT SAME text sent by the user"""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text},
    ]
    gpt_audio_response = client.chat.completions.create(
        model="gpt-4o-mini-audio-preview",
        messages=messages,
        modalities=["text", "audio"],
        audio={
            "voice": "sage",
            "format": "mp3",
        },
    )

    print(
        f"Time waiting for GPT to generate audio from text to play audio {time.perf_counter() - start}s"
    )

    audio_base64 = gpt_audio_response.choices[0].message.audio.data
    play_audio_from_base64(audio_base64)
