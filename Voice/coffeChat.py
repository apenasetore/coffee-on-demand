import time
import asyncio
import edge_tts
import io
import voice_detection as vd
import os
import json
import tempfile
import pygame

from gtts import gTTS
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()
API_KEY = os.getenv("API_KEY")
client = OpenAI(
  api_key=API_KEY,
)
class ResponseFormat(BaseModel):
    inPhase: bool
    message: str

class ResponseStopFormat(BaseModel):
    stop: bool
    message: str
    reason: str


def transcribe_audio(file_path):
    audio_file = open(file_path,"rb")
    file = io.BufferedReader(audio_file)
    print(audio_file)
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=file,
        language='en'
    )
    return transcript.text

def get_typed_input(prompt="Enter your input: "):
    """
    Prompts the user to type input from the terminal.
    
    Args:
        prompt (str): The message displayed to the user.
    
    Returns:
        str: The text entered by the user.
    """
    try:
        # Prompt the user and return their input
        return input(prompt)
    except KeyboardInterrupt:
        print("\nInput interrupted. Exiting.")
        return None  # Return None if the user interrupts



def has_to_stop(messages, phase_prompt):
    # print("Messages",messages)
   
    
    response = client.beta.chat.completions.parse(
                model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f'''You are a coffee grain vending machine with 4 types of grains available. 
                         You provide only coffee grains and can register users with their consent.  
                         Respond to this text according to the phase instructions: 
                         {phase_prompt}.  
                         Continue this conversation with the user.
                         '''}  
                        ] + (messages if len(messages) else []),
                    
                response_format=ResponseStopFormat
    )
    response = json.loads(response.choices[0].message.content)
    # print(response)
    in_phase = response['stop']
    message = response['message'] 
    reason = response['reason']
    # print(in_phase, message)
    # print('Message',message)
    return in_phase, message, reason


# Function to generate a response using ChatGPT
def generate_response(messages, phase_prompt):
    # print("Messages",messages)
    response = client.beta.chat.completions.parse(
                model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f'''You are a coffee grain vending machine with 4 types of grains available.  
                        Respond to this text according to the phase instructions. 
                        {phase_prompt}.
                        Continue this convesation with the user.
                        '''}
                        ] + (messages if len(messages) else []),
                    
                response_format=ResponseFormat
    )
    response = json.loads(response.choices[0].message.content)
    # print(response)
    in_phase = response['inPhase']
    message = response['message'] 
    # print(in_phase, message)
    # print('Message',message)
    return in_phase, message

def speak_message(message):
    # Generate TTS audio using gTTS
    print('This will be speaked', message)
    audio = gTTS(text=message, lang='en', slow=False)

    # Save the audio to a temporary file
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as temp_audio:
        audio.save(temp_audio.name)  # Save TTS output

        # Initialize pygame mixer
        pygame.mixer.init()

        # Load and play the MP3 file
        pygame.mixer.music.load(temp_audio.name)
        pygame.mixer.music.play()

        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pass
   



def append_message(role, content):
    messages.append({"role": role, "content": content})     

if __name__ == "__main__":

    phase_prompt = [
    {
        "name": "IntroductionState",
        "goal": "Present to the user and ask how you can help.",
        "guideline": "Say hello and welcome the guest to the machine. Keep the conversation natural. Call them by their name, if in client mode. "
    },
    {
        "name": "AvailableCoffeeState",
        "goal": "Figure out what is the user's coffee of interest.",
        "guideline": "Generata e message that tells to the customer the available coffee grains.You can use the database to see previous purchases, if known, or to get more information on a specific type of coffee. "
    },
    {
        "name": "QuantityState",
        "goal": "Get how much of the coffee the consumer wants, considering the bounds.",
        "guideline": "Ask about the quantity of grams the user wants. The limit is from 20 to 300 grams. Do not allow the user to get out of those bounds."
    },
    {
        "name": "PaymentState",
        "goal": "Get confirmation from the user about the order and payment.",
        "guideline": "Confirm the order with the user by repeating it for them. Tell the price and ask for confirmation."
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
        "name": "Iconmpatível",
        "goal": "Determine if the user is asking something that is not relayted to coffee or available. Keep in mind that coffee grains is refered as coffee",
        "guideline": "Say that the machine does not provide what the user wants, the reason why and  to try again later"
    },
    {
        "name": "Desinterested",
        "goal": "The user explicetly said he does not wwant to buy anything related to coffe.",
        "guideline": "Say goodbye to the customer."
    }
    ]


    messages = []
    stop = False
    flag = False

    while(not stop):
        for state in phase_prompt:    
            print('State')
            prompt = f"Verify if the current phase is {state['name']}. The phase's goal is {state['goal']}. Return true in inPhase in case the phase goal has not been accomplished. Return false in case the objective has been accomplished. To reach the goal, you must {state['guideline']}."
            
            in_phase, message =  generate_response(messages, prompt)
            if (in_phase):
                print(f"State: {state['name']}")
                print(f"Goal: {state['goal']}")
                print(f"Guideline: {state['guideline']}")
                print("\n")
                append_message('system',message)
                print(messages)
                break
        if flag:
            for sp in stop_prompt:
                prompt = f"Verify if the current the reason to stop is {sp['name']}. To determine that  {sp['goal']}. Return true in stop in case the conversation must stop. To determine it, you must {sp['guideline']}., only generate a message if stop is True"
                stop, message, reason = has_to_stop(messages,prompt)
                
                if stop:
                    append_message('system', message)
                    print(f"State: {sp['name']}")
                    print(f"Goal: {sp['goal']}")
                    print(f"Guideline: {sp['guideline']}")
                    print("\n")

                    append_message('system',message)
                    break    

        flag = True
        print('Message', message)
        speak_message(message)
        print(message)
        if not stop:
            vd.voice_detection()
            transcription = transcribe_audio('gravacao.wav')
            # transcription = get_typed_input()
            print('Transcription',transcription)
            append_message('user', transcription)
            # print(stop)
    
        
        
       
        
        
        