import time
import asyncio
import edge_tts
import io
import voice_detection as vd
import os
import json

from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()
API_KEY = os.getenv("API_KEY")
client = OpenAI(
  api_key=API_KEY,
)


def transcribe_audio(file_path):
    audio_file = open(file_path,"rb")
    file = io.BufferedReader(audio_file)
    print(audio_file)
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=file
    )
    return transcript.text


# Function to generate a response using ChatGPT
def generate_response(messages, phase_prompt):

    class ResponseFormat(BaseModel):
        inPhase: bool
        message: str
    
    response = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f'''You are a coffee grain vending machine with 4 types of grains available. 
                     Respond to this text according to the phase instructions. 
                     {phase_prompt}.
                     Continue this convesation with the user.
                     {messages}'''},
                    ],
                response_format=ResponseFormat
    )
    response = json.loads(response.choices[0].message.content)
    print(response)
    in_phase = response['inPhase']
    message = response['message'] 
    print(in_phase, message)
    return in_phase, message

# Function to convert text to speech using OpenAI's TTS API
def synthesize_speech(text):
    filename = '/home/etore/CoffeOnDemand/responde4.mp3'
    VOICES = []
    
    communicate = edge_tts.Communicate(text, )
    
    # Set properties (optional)
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)

    # Save speech to a file
    engine.save_to_file(text, filename)
    engine.runAndWait()

    print(f"Saved to {filename}")
    
# Main function to bring it all together
def main(file_path):
 
    # Step 1: Transcribe the audio
    start_time = time.time()
    transcription = transcribe_audio(file_path)
    print("Transcription:", transcription)
    end_time_1 = time.time()
    print('Transcription Time',end_time_1-start_time)

    # Step 2: Generate a response based on the transcription
    response_text = generate_response(transcription)
    print("Response:", response_text)
    end_time_2 = time.time()
    print('Generate Time Time',end_time_2-end_time_1)
    
    # # Step 3: Synthesize the response as audio
    # synthesize_speech(response_text)
    # end_time_3 = time.time()
    # print('Synthesize T
    # ime',end_time_3-end_time_2)
    # print('All Time',end_time_3-start_time)
        

if __name__ == "__main__":

    prompt = [
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

    messages = []
    for state in prompt:
        print(messages)
        print(f"State: {state['name']}")
        print(f"Goal: {state['goal']}")
        print(f"Guideline: {state['guideline']}")
        print("\n")
        phase_prompt = f"Verify if the current phase is {state['name']}. The phase's goal is {state['goal']}. Return true in inPhase in case the phase goal has not been accomplished. Return false in case the objective has been accomplished. To reach the goal, you must {state['guideline']}."
        
        in_phase, message = generate_response(messages, phase_prompt)
        if (in_phase):
            messages.append(f"Machine: {message}")
            print(messages)
        else:
            break
        
        vd.voice_detection()
        transcription = transcribe_audio('gravacao.wav')
        print(transcription)
        messages.append(f"Client: {transcription}")

        
        