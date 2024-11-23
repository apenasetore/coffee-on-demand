import queue
import threading
import time
from hx711 import HX711

DT_PIN = 5
SCK_PIN = 6


def dispense_task(measure_coffee_queue: queue.Queue, coffee_container, turn_on_motor_event_flag: threading.Event):
    hx = HX711(DT_PIN, SCK_PIN)
    hx.set_reading_format("MSB", "MSB")
    hx.reset()
    hx.tare()

    while True:
        
        measure_coffee_request = measure_coffee_queue.get()

        container_id = measure_coffee_request["container"]
        with coffee_container.get_lock():
            coffee_container.value = container_id

        requested_coffee_weight = measure_coffee_request["weight"]
        turn_on_motor_event_flag.set()

        while weight <= requested_coffee_weight: 
            weight = max(0,int(hx.get_weight(5)))
            hx.power_down()
            hx.power_up()
            time.sleep(0.1)

        turn_on_motor_event_flag.clear()
        


        

