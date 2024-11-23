import threading
import multiprocessing
import time
import queue
from embedded.audio import capture_audio, play_audio
from embedded.client_recognition import recognize_customer, generate_new_encodings
from embedded.motors import motor_task

if __name__ == "__main__":
    audio_queue = queue.Queue()
    rebuild_binaries_event = threading.Event

    turn_on_motor_event_flag = threading.Event
    coffee_container = multiprocessing.Value('i', 1)

    print("Queue init")
    threading.Thread(target=capture_audio, daemon=True, args=(audio_queue,)).start()
    threading.Thread(target=motor_task, daemon=True, args=(turn_on_motor_event_flag, coffee_container))
    #threading.Thread(target=play_audio, daemon=True, args=(audio_queue,)).start()
    #threading.Thread(target=recognize_customer, daemon=True).start()
    #threading.Thread(target=generate_new_encodings, daemon=True, args=(rebuild_binaries_event,)).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Finishing...")