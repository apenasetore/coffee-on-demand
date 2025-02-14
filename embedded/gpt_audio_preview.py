import io
import json
import multiprocessing
import os
import time
import tempfile
from dotenv import load_dotenv
import pyaudio
import time
import wave
from embedded.gpt_dtos.dto import (
    GPTDataResponse,
    GPTRegistrationDataResponse,
    GPTStage,
)
import openai
import time

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
STREAM_RESPONSE = True

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
        filtered_coffees = [coffee for coffee in coffees if coffee["stock_grams"] > 0]

        print(f"Time fetching CoffeeAPI info {time.perf_counter() - start}s")

        name = customer_info.get("firstname") if customer_info else "coffee enthusiast"

        first_stage_prompt = f"""You are a coffee vending machine that sells coffee grains. For the response, always generate audio. 
            Follow the instructions below:  
            - You are selling in Reais, Brazil's currency. Do not speak portuguese.
            - Coffee price is calculated per gram (provide the total price).
            - Coffees available and information: {json.dumps(filtered_coffees)}
            - Coffee weight range is between 20g and 300g
            - Your task is to analyze the conversation history and identify in what phase it is
            - Phases of conversation: {phases}
            - Answer in an concise way, very small text, without topics and DO NOT MENTION the phases in response.
            You need to read the conversation check if all necessary information has been gotten.
            
            Remember to fill obrigatory fields:
            
            - chosen_coffee_weight
            - container_number (is the number of the container where the chosen coffee is located at)
            - total_price
            - order_confirmed (if and only if the client confirm its order. Do not set it as true if assistant ask and the client didnt answer)
            
            Additional details:
            - Client's name: {name}
            - Purchase history: {json.dumps(purchase_history) if purchase_history else 'This client has no purchase history'}."""

        conversation_history = []
        text_conversation_history = []
        proceed_to_payment = False
        while True:
            
            start = time.perf_counter()
            gpt_data_response = generate_machine_response(
                first_stage_prompt, conversation_history
            )
            
            conversation_history.append({"role": "assistant", "content": gpt_data_response.response})
            print(f"Response in {time.perf_counter() - start}s: {gpt_data_response}")
            play_audio(gpt_data_response.response)
            
            if gpt_data_response.order_confirmed:
                proceed_to_payment = True
                break

            try:
                capture_audio_event_flag.set()
                send_to_arduino("UPDATE:STATE:LISTENING")
                audio_buffer = audio_queue.get(timeout=20)
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
            play_audio("Please scan the QR Code in the LCD screen to pay. I will wait for 1 minute")
            send_to_arduino(f"UPDATE:PRICE:{int(gpt_data_response.total_price * 100)}")
            send_to_arduino(f"UPDATE:PIX:{pix['payload']['payload']}")

            try:
                payment_waiting = 0
                payment = verify_payment(pix["paymentId"])
                while not payment["paid"]:
                    payment = verify_payment(pix["paymentId"])
                    time.sleep(3)
                    payment_waiting += 3
                    if payment_waiting >= 60:
                        break

                if payment_waiting >= 60:
                    play_audio("Oh, I think you are not here anymore. Let's move on.")
                    recognize_customer_event_flag.set()
                    continue
            except Exception as e:
                print(f"Payment failed: {e}")
                play_audio("Oh, something wrong occurred with your payment, sorry.")
                recognize_customer_event_flag.set()
                continue

            chosen_coffee = None
            for coffee in filtered_coffees:
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

def generate_machine_response(system_prompt: str, conversation_history: list[dict], stage: GPTStage = GPTStage.NORMAL_FLOW) -> GPTDataResponse | GPTRegistrationDataResponse:
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=messages,
        response_format=(
            GPTDataResponse
            if stage == GPTStage.NORMAL_FLOW
            else GPTRegistrationDataResponse
        ),
    )

    response_data = json.loads(response.choices[0].message.content)
    return (
        GPTDataResponse(**response_data)
        if stage == GPTStage.NORMAL_FLOW
        else GPTRegistrationDataResponse(**response_data)
    )

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


def play_audio(text: str):
    send_to_arduino("UPDATE:STATE:TALKING")

    if STREAM_RESPONSE:
        print("Streaming audio")
        player_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
        stream_start = False
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="echo",
            input=text,
            response_format='pcm'
        ) as response:
            silence_threshold = 0.01
            for chunk in response.iter_bytes(chunk_size=1024):
                if stream_start:
                    player_stream.write(chunk)
                else:
                    if max(chunk) > silence_threshold:
                        player_stream.write(chunk)
                        stream_start = True
        
        player_stream.close()
    else:
        start = time.perf_counter()
        print("Waiting audio")
        audio_buffer = b''
        response = client.audio.speech.create(
            model="tts-1",
            voice="echo",
            input=text,
            response_format='pcm'
        )

        for chunk in response.iter_bytes(chunk_size=1024):
            audio_buffer += chunk

        p = pyaudio.PyAudio()
        player_stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
        player_stream.write(audio_buffer)
        print(f"Time waiting audio: {time.perf_counter() - start}")
        player_stream.close()
        p.terminate()
