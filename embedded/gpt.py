import multiprocessing
import time
import tempfile
from gtts import gTTS
import pyaudio
from playsound import playsound

from embedded.audio import CHANNELS, FORMAT, RATE


def generate_response(customer_queue: multiprocessing.Queue, audio_queue: multiprocessing.Queue, capture_audio_event_flag, recognize_customer_event_flag):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True)
    
    finished_conversation = False
    while True:
        customer = customer_queue.get()
        print(f"GPT task received info that customer {customer} arrived")
        time.sleep(1)
        
        text = f"Hello {customer}! It's nice to have you in my store, how can i help you today?"
        audio = gTTS(text=text, lang='en', slow=False)
        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as temp_audio:
            audio.save(temp_audio.name)
            playsound(temp_audio.name)

        time.sleep(1)
        capture_audio_event_flag.set()

        while not finished_conversation:
            try:
                audio_buffer = audio_queue.get(timeout=10)
            except Exception as e:
                print("No response given by the customer, restarting flow")
                capture_audio_event_flag.clear()
                recognize_customer_event_flag.set()
                break

            print(f"Hello {customer}, I'm GPT and received this audio!")
            time.sleep(3)
            audio_buffer.seek(0)
            stream.write(audio_buffer.read())
            print("Finished audio")
            capture_audio_event_flag.set()