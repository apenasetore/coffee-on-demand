import io
import queue
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

def capture_audio(audio_queue: queue.Queue):
    p = pyaudio.PyAudio()

    vad = webrtcvad.Vad()
    vad.set_mode(2) 
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    audio_buffer = io.BytesIO()
    recording = False
    silent = 0
    while True:
        data = stream.read(CHUNK)

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
                    print("End of speech")
                    break

    print("Saving audio")
    audio_buffer.seek(0)
    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(audio_buffer.read())


def play_audio(audio_queue: queue.Queue):
    # p = pyaudio.PyAudio()
    # stream = p.open(format=FORMAT,
    #                 channels=CHANNELS,
    #                 rate=RATE,
    #                 output=True)
    
    while True:
        audio_buffer = audio_queue.get()
        print("Received audio in queue")   
        with wave.open("sound.wav", "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(audio_buffer.read())     
        #stream.write(audio_buffer.read())
    
    stream.stop_stream()
    stream.close()
    p.terminate()