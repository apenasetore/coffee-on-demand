import threading
import multiprocessing
import time
import queue
#from embedded.audio import capture_audio, play_audio
#from embedded.client_recognition import recognize_customer, generate_new_encodings
from embedded.motors import motor_task
from embedded.measure_coffee import dispense_task


if __name__ == "__main__":
    audio_queue = queue.Queue()
    rebuild_binaries_event = multiprocessing.Event()

    turn_on_motor_event_flag = multiprocessing.Event()
    coffee_container = multiprocessing.Value('i', 1)
    measure_coffee_queue = multiprocessing.Queue()

    turn_on_motor_event_flag.clear()
    #threading.Thread(target=capture_audio, daemon=True, args=(audio_queue,)).start()
    multiprocessing.Process(target=motor_task, daemon=True, args=(turn_on_motor_event_flag, coffee_container)).start()
    multiprocessing.Process(target=dispense_task, daemon=True, args=(measure_coffee_queue, coffee_container, turn_on_motor_event_flag)).start()
    #threading.Thread(target=play_audio, daemon=True, args=(audio_queue,)).start()
    #threading.Thread(target=recognize_customer, daemon=True).start()
    #threading.Thread(target=generate_new_encodings, daemon=True, args=(rebuild_binaries_event,)).start()

    try:
        while True:
            print("Initing order")
            time.sleep(2)
            measure_coffee_queue.put({"container_id": 1, "weight": 100})
            time.sleep(10000)
    except KeyboardInterrupt:
        print("Finishing...")