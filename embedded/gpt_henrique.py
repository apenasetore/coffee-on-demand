import asyncio
import io
import json
import multiprocessing
import os
import time
import tempfile
from dotenv import load_dotenv
import time
from gtts import gTTS
import wave
from embedded.gpt_dtos.dto import GPTInteraction
import openai
import subprocess
import time
import pyttsx3

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
client = openai.AsyncOpenAI(api_key=API_KEY)


def generate_response(
    customer_queue: multiprocessing.Queue,
    audio_queue: multiprocessing.Queue,
    measure_coffee_queue: multiprocessing.Queue,
    capture_audio_event_flag,
    recognize_customer_event_flag,
):
    asyncio.run(
        generate_response_async(
            customer_queue,
            audio_queue,
            measure_coffee_queue,
            capture_audio_event_flag,
            recognize_customer_event_flag,
        )
    )


async def generate_response_async(
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

        main_prompt = f"""You are a coffee vending machine that sells coffee grains. Follow the instructions below:  
            - You are selling in Reais, Brazil's currency. Do not speak portuguese.
            - Coffee price is calculated per gram (provide the total price).
            - Coffees available: {json.dumps(coffees)}
            - Your task is to analyze the conversation history and identify in what phase it is
            - Phases of conversation: {phases}
            - Answer in an concise way, very small text, without topics and do not use '/' or '*' in answer.
            
            Additional details:
            - Client's name: {name}
            - Purchase history: {json.dumps(purchase_history) if purchase_history else 'This client has no purchase history'}."""

        conversation_history = []
        proceed_to_payment = False
        while True:

            start = time.perf_counter()
            gpt_response = await request(main_prompt, conversation_history)
            print(f"Time checking main phases {time.perf_counter() - start}s")
            print(gpt_response)

            conversation_history.append(
                {"role": "assistant", "content": gpt_response.response}
            )

            play_audio(gpt_response.response)
            if gpt_response.order_confirmed:
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

            user_response = await transcript(audio_buffer)
            conversation_history.append({"role": "user", "content": user_response})

        if proceed_to_payment:
            print(f"Finished conversation, generating pix and waiting for deposit.")
            pix = create_payment(gpt_response.total_price)
            play_audio("Please scan the QR Code in the LCD screen to pay.")
            send_to_arduino(f"UPDATE:PIX:{pix['payload']['payload']}")
            payment = verify_payment(pix["paymentId"])
            while not payment["paid"]:
                print(payment["paid"])
                payment = verify_payment(pix["paymentId"])
                time.sleep(3)

            chosen_coffee = None
            for coffee in coffees:
                if coffee["container"] == str(gpt_response.container_number):
                    chosen_coffee = coffee["id"]
                    break

            print(
                f"Finished conversation, putting order of container {gpt_response.container_number}, {gpt_response.chosen_coffee_weight} grams."
            )

            play_audio("Payment confirmed! Let's dispense!")

            measure_coffee_queue.put(
                {
                    "container_id": gpt_response.container_number - 1,
                    "weight": gpt_response.chosen_coffee_weight,
                    "customer_id": customer,
                    "coffee_id": chosen_coffee,
                }
            )


async def request(system_prompt: str, conversation_history: list[dict]):
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    response = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=messages,
        response_format=GPTInteraction,
    )
    response = json.loads(response.choices[0].message.content)

    return GPTInteraction(**response)


async def transcript(audio: list) -> str:
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
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=file,
            language="en",
            prompt="Reais, Etore, Henrique, Maria Luiza, Francisco, Felipe, Heitor",
        )
        user_response = transcript.text
        print(f"Time to transcript in whisper = {time.perf_counter() - start}s")

    print(f"User said: {user_response}")
    return user_response


# def play_audio(text: str):
#     print("Text to speech...")
#     start = time.perf_counter()
#     audio = gTTS(text=text, lang="en", slow=False)
#     print(f"Time to complete TTS = {time.perf_counter() - start}s")
#     audio_bytes = io.BytesIO()

#     start = time.perf_counter()
#     audio.write_to_fp(audio_bytes)
#     print(f"Time writing bytes to variable = {time.perf_counter() - start}s")
#     audio_bytes.seek(0)

#     pygame.mixer.init()
#     start = time.perf_counter()
#     pygame.mixer.music.load(audio_bytes, "mp3")
#     print(f"Time to load audio in pygame = {time.perf_counter() - start}s")
#     pygame.mixer.music.play()
#     send_to_arduino("UPDATE:STATE:TALKING")
#     while pygame.mixer.music.get_busy():
#         time.sleep(0.3)

#     print("Finished playing sound")


# ##play audio deepssek
# async def play_audio(text: str):
#     print("Text to speech...")

#     # Start TTS timing
#     start = time.perf_counter()

#     # Send state to Arduino *before* speech starts
#     send_to_arduino("UPDATE:STATE:TALKING")

#     # Use espeak asynchronously
#     process = await asyncio.create_subprocess_exec(
#         "espeak",
#         "-ven+f3",  # English voice, female variant 3
#         "-s175",     # Speed: 175 words per minute
#         text,
#         stdout=asyncio.subprocess.DEVNULL,  # Ignore stdout
#         stderr=asyncio.subprocess.DEVNULL   # Ignore stderr
#     )

#     # Wait for the process to complete
#     await process.wait()


def play_audio(text: str):
    print("Text to speech...")
    text = text.replace("*", "")
    # Start TTS timing
    start = time.perf_counter()

    # Send state to Arduino before speech starts
    send_to_arduino("UPDATE:STATE:TALKING")

    # Use espeak in a blocking manner
    subprocess.run(
        [
            "espeak",
            "-ven+f3",  # English voice, female variant 3
            "-s150",  # Speed: 175 words per minute
            text,
        ],
        check=True,
    )  # `check=True` ensures errors are raised

    print(f"Total TTS + Playback Time = {time.perf_counter() - start:.2f}s")
    print("Finished playing sound")
