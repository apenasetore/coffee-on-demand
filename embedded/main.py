import threading
import time
import queue
from embedded.audio import capture_audio
from embedded.audio import play_audio

if __name__ == "__main__":
    audio_queue = queue.Queue()
    print("Queue init")
    threading.Thread(target=capture_audio, daemon=True, args=(audio_queue,)).start()
    threading.Thread(target=play_audio, daemon=True, args=(audio_queue,)).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Finishing...")