import time
import asyncio
import edge_tts
import io
import voice_detection as vd
import os

from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI


load_dotenv()
API_KEY = os.getenv("API_KEY")
print(API_KEY)
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
    print(transcript.text)
    return transcript.text


# Function to generate a response using ChatGPT
def generate_response(transcription):
    prompt = f"The user said: '{transcription}'. Please respond to this appropriately."
    
    response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a coffee grain vending machine with 4 types of grains available repond to this text."},
                    {"role": "user", "content": transcription}
                    ]
                )
    print(response.choices[0].message.content)
    return response.choices[0].message.content

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
        

        # Example usage
vd.voice_detection()
main("gravacao.wav")
