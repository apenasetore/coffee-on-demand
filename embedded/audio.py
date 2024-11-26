import io
import multiprocessing
import queue
import time
import numpy as np
import wave

import pyaudio
import webrtcvad

CHUNK_DURATION_MS = 30
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = int(RATE * CHUNK_DURATION_MS / 1000)
OUTPUT_FILENAME="nao_sei.wav"

def amplify_audio(data, amplification_factor):
    amplified_data = data * amplification_factor
    
    amplified_data = np.clip(amplified_data, -32768, 32767)
    
    return amplified_data

def capture_audio(audio_queue: multiprocessing.Queue, capture_audio_event_flag):
    p = pyaudio.PyAudio()

    vad = webrtcvad.Vad()
    vad.set_mode(3) 
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    while True:

        audio_buffer = io.BytesIO()
        recording = False
        silent = 0

        while capture_audio_event_flag.is_set():
            data = stream.read(CHUNK, exception_on_overflow=False)

            if recording:
                print("Appeding speech")
                audio_data_np = np.frombuffer(data, dtype=np.int16)
                amplified_audio = amplify_audio(audio_data_np, amplification_factor=10.0)
                amplified_bytes = amplified_audio.astype(np.int16).tobytes()
                audio_buffer.write(amplified_bytes)

            is_speech = vad.is_speech(data, RATE)
            if is_speech and not recording:
                recording = True

            if is_speech:
                silent = 0
            else:
                if recording:
                    silent += 1
                    if silent >= 50:
                        recording = False
                        silent = 0
                        print("End of speech")
                        capture_audio_event_flag.clear()
                        audio_queue.put(audio_buffer)
                        audio_buffer = io.BytesIO()
