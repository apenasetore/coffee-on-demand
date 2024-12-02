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
from openai import OpenAI

from embedded.audio import CHANNELS, RATE
from embedded.coffee_api.api import get_purchases, get_coffees

load_dotenv()
API_KEY = os.getenv("API_KEY")
client = OpenAI(api_key=API_KEY)

def generate_response(customer_queue: multiprocessing.Queue, audio_queue: multiprocessing.Queue, measure_coffee_queue: multiprocessing.Queue, capture_audio_event_flag, recognize_customer_event_flag):
    phase_prompt = [
        {
            "name": "IntroductionState",
            "goal": "Present to the user and ask how you can help.",
            "guideline": "Say hello and welcome the guest to the machine. Keep the conversation natural. Call them by their name, if in client mode."
        },
        {
            "name": "AvailableCoffeeState",
            "goal": "Figure out what is the user's coffee of interest.",
            "guideline": "Talk to the user about which of the available coffees suits their taste. You can use the database to see previous purchases, if known, or to get more information on a specific type of coffee."
        },
        {
            "name": "QuantityState",
            "goal": "Get how much of the coffee the consumer wants, considering the bounds.",
            "guideline": "Ask about the quantity of grams the user wants. The limit is from 20 to 300 grams. Do not allow the user to get out of those bounds. Also, use coffee information to see how much coffee is in stock through the stock_grams field. Do not let the user order more than the amount in stock."
        },
        {
            "name": "PaymentState",
            "goal": "Get confirmation from the user about the order and payment.",
            "guideline": "Confirm the order with the user by repeating it for them. Tell the price and ask for confirmation. Returns in quantity the amount of coffee the user required"
        },
        {
            "name": "RegisterState",
            "goal": "Get first and last name of the customer.",
            "guideline": "Ask if the guest wants to register as a customer; if not, close the phase. If yes, get their first and last name."
        },
        {
            "name": "GoodbyeState",
            "goal": "Finish order and say goodbye.",
            "guideline": "Say goodbye to the customer."
        }
    ]
    stop_prompt = [
        {
            "name": "Incompatible",
            "goal": "Determine if the user is asking something that is not coffee or available.",
            "guideline": "Say that the machine does not provide what the user wants, the reason why and to try again later"
        },
        {
            "name": "Desinterested",
            "goal": "The user is not more interested in buying coffee.",
            "guideline": "Say goodbye to the customer.",
        }
    ]
    
    while True:
        customer = customer_queue.get()
        finished_conversation = False
        print(f"GPT task received info that customer {customer} arrived")
        purchases = get_purchases(customer)
        customer_info = purchases.get("customer")
        purchase_history = purchases.get("purchases")
        coffees = get_coffees(only_active=True)

        history = []
        while not finished_conversation:
            for state in phase_prompt:    
                prompt = f"""Verify if the current phase is {state['name']}. The phase's goal is {state['goal']}. 
                        Return true in inPhase in case the phase goal has not been accomplished. Return false in case the objective has been accomplished. 
                        To reach the goal, you must {state['guideline']}. 
                        If in client mode, client's name is {customer_info.get('firstname')} and their purchase history is {json.dumps(purchase_history) if purchase_history else '[]'}. 
                        If he wants to register, return True in want_to_register, else return False. Be objective in responses, with minimum words."""
                
                confirmed_quantity = 0
                in_phase, response, quantity = request(coffees, history, prompt, None)
                if (in_phase):
                    print(f"State: {state['name']}")
                    print(f"Goal: {state['goal']}")
                    print(f"Guideline: {state['guideline']}")
                    print(f"Response: {response}")
                    history.append({"role": "system", "content": response})
                    if state["name"] == "PaymentState":
                        confirmed_quantity = quantity
                        print(f"Saving quantity of {confirmed_quantity} grams")

                    if state["name"] == "GoodbyeState":
                        finished_conversation = True

                    break
                
            play_audio(response)
            if finished_conversation:
                print(f"Finished conversation, putting order of {confirmed_quantity} in to dispense queue")
                measure_coffee_queue.put({"container_id": 1, "weight": confirmed_quantity})
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
                stop, response, reason = has_to_stop(history, prompt)

                if stop:
                    print(f"State: {sp['name']}")
                    print(f"Goal: {sp['goal']}")
                    print(f"Guideline: {sp['guideline']}")
                    history.append({"role": "system", "content": response})
                    play_audio(response)
                    finished_conversation = True
                    recognize_customer_event_flag.set()
                    break

def request(coffees : list, history: list, phase_prompt: str, purchase_history: list) -> tuple:
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
            messages=[
                {"role": "system", "content": f'''You are a coffee grain vending machine with these coffee grains available: {json.dumps(coffees)}.  
                Respond to this text according to the phase instructions. 
                {phase_prompt}.
                Continue this convesation with the user.
                The user's purchase history is {json.dumps(purchase_history) if purchase_history else "[]"}
                '''}
                ] + (history if len(history) else []),
            
        response_format=ResponseFormat
    )
    response = json.loads(response.choices[0].message.content)

    in_phase = response["in_phase"]
    message = response["message"]
    quantity = response["quantity"] 

    return in_phase, message, quantity

def has_to_stop(coffees: list, history: list, phase_prompt: str) -> tuple:
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
            messages=[
                {"role": "system", "content": f'''You are a coffee grain vending machine with these coffee grains available: {json.dumps(coffees)}. 
                    You provide only coffee grains and can register users with their consent.  
                    Respond to this text according to the phase instructions: 
                    {phase_prompt}.  
                    Continue this conversation with the user.
                    '''}  
                ] + (history if len(history) else []),
            
        response_format=ResponseStopFormat
    )
    response = json.loads(response.choices[0].message.content)
    stop = response['stop']
    message = response['message'] 
    reason = response['reason']

    return stop, message, reason

def transcript(audio: list) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        with wave.open(temp_audio_file, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b''.join(audio))
        
        temp_audio_file.seek(0)
        file = io.BufferedReader(open(temp_audio_file.name, 'rb'))
        
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=file,
            language="en"
        )
        user_response = transcript.text

    print(f"User said: {user_response}")
    return user_response

def play_audio(text: str):
    print("Text to speech...")
    audio = gTTS(text=text, lang='en', slow=False)
    print("Completed transformation")
    pygame.mixer.init()
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as temp_audio:
        audio.save(temp_audio.name)
        pygame.mixer.music.load(temp_audio.name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.3)

    print("Finished playing sound")