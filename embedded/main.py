import threading
import multiprocessing
import time
import queue
from embedded.audio import capture_audio
from embedded.client_recognition import recognize_customer, generate_new_encodings
from embedded.gpt import generate_response
#from embedded.motors import motor_task
#from embedded.measure_coffee import dispense_task


if __name__ == "__main__":
    rebuild_binaries_event_flag = multiprocessing.Event()
    recognize_customer_event_flag = multiprocessing.Event()
    turn_on_motor_event_flag = multiprocessing.Event()
    capture_audio_event_flag = multiprocessing.Event()

    coffee_container = multiprocessing.Value('i', 1)

    measure_coffee_queue = multiprocessing.Queue()
    customer_queue = multiprocessing.Queue()
    audio_queue = multiprocessing.Queue()
    
    turn_on_motor_event_flag.clear()
    #multiprocessing.Process(target=motor_task, daemon=True, args=(turn_on_motor_event_flag, coffee_container)).start()
    #multiprocessing.Process(target=dispense_task, daemon=True, args=(measure_coffee_queue, coffee_container, turn_on_motor_event_flag)).start()
    multiprocessing.Process(target=recognize_customer, args=(recognize_customer_event_flag, customer_queue), daemon=True).start()
    multiprocessing.Process(target=capture_audio, daemon=True, args=(audio_queue, capture_audio_event_flag)).start()
    multiprocessing.Process(target=generate_response, daemon=True, args=(customer_queue, audio_queue, measure_coffee_queue, capture_audio_event_flag, recognize_customer_event_flag)).start()

    try:
        while True:
            print("System on in 5 seconds")
            time.sleep(5)
            recognize_customer_event_flag.set()
            time.sleep(100000)
    except KeyboardInterrupt:
        print("Finishing...")