import pyaudio
import webrtcvad
import io
import time
import requests
import wave
import subprocess
import os
from openai import OpenAI
from pydub import AudioSegment
from gtts import gTTS
from voice_detection import voice_detection


CHUNK_DURATION_MS = 30
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK = int(RATE * CHUNK_DURATION_MS / 1000)

p = pyaudio.PyAudio()
vad = webrtcvad.Vad()
vad.set_mode(3) 

client = OpenAI(
  api_key='',
)

def play_audio(audio_file):

    headers = {
    "Authorization":  "Bearer ",
    }

    files = {
        "file": ("audio.mp3", audio_file, "audio/mp3") 
    }

    json = {
        "model": "whisper-1",
        "language": "en"
    }
    url = 'https://api.openai.com/v1/audio/transcriptions'

    start_time = time.time()
    req = requests.post( url,headers=headers, data=json, files=files)
    print(req)
    results = req.json()['text']
    time2 = time.time()
    print(results)
    print(f"Elapsed time: {time2 - start_time}")
    
    #Create Response
    prompt = f"The user said: '{results}'. Please respond to this appropriately."
   
    response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a coffee grain vending machine with 4 types of grains available repond to this text."},
                    {"role": "user", "content": results}
                    ]
                )

    time3 = time.time()
    print(f"Elapsed time2: {time3 - time2}")
    text = response.choices[0].message.content
    print(text)
    tts = gTTS(text)
    tts.save("hello.mp3")
    # response = client.audio.speech.create(
    #     model="tts-1",
    #     voice="echo",
    #     input=text
    # )
    time4 = time.time()
    print('Time for response:',time4-time3)
    print(time4-start_time)
    # response.stream_to_file()

    
def listen_mic():
    stream = p.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK,input_device_index=0)

    audio_buffer = io.BytesIO()
    recording = False

    print("Listening...")

    try:
        while True:
            frame = stream.read(CHUNK)
            is_speech = vad.is_speech(frame, RATE)

            if is_speech:
                if not recording:
                    print("Speech detected")
                    recording = True
                    audio_buffer = io.BytesIO()

                audio_buffer.write(frame)
                print("Writing audio into buffer")
            else:
                if recording:
                    print("End of speech detected")
                    recording = False
                    audio_buffer.seek(0)
                    audio_segment = AudioSegment.from_raw(
                        audio_buffer, 
                        frame_rate=RATE, 
                        channels=CHANNELS,
                        sample_width=2
                    )                    
                    # Create an in-memory MP3 file
                    audio_mp3 = io.BytesIO()
                    audio_segment.export(audio_mp3, format="mp3")
                    # saving this mp3 
                    with open("gravacao.mp3", "wb") as f:
                        f.write(audio_mp3.read())
                    # play_audio(audio_buffer)
                    audio_buffer = io.BytesIO()

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        stream.stop_stream()
        stream.close()

def detect_and_record_voice():
    voice_detection()
    play_audio("gravacao.wav")

if __name__ == "__main__":
    detect_and_record_voice()
    # for i in range(p.get_device_count()):
    #     device_info = p.get_device_info_by_index(i)
    #     print(f"Device {i}: {device_info['name']}")
    #     print(f"  Max Input Channels: {device_info['maxInputChannels']}")
    #     print(f"  Default Sample Rate: {device_info['defaultSampleRate']}")