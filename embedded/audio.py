import io
import queue
import time

import pyaudio
import webrtcvad

CHUNK_DURATION_MS = 30
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = int(RATE * CHUNK_DURATION_MS / 1000)

def capture_audio(audio_queue: queue.Queue):
    p = pyaudio.PyAudio()
    vad = webrtcvad.Vad()
    vad.set_mode(3) 
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    audio_buffer = io.BytesIO()
    recording = False
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
                audio_queue.put(audio_buffer)
                audio_buffer = io.BytesIO()


def play_audio(audio_queue: queue.Queue):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True)
    
    while True:
        audio_buffer = audio_queue.get()
        print("Received audio in queue")        
        stream.write(audio_buffer.read())
    
    stream.stop_stream()
    stream.close()
    p.terminate()