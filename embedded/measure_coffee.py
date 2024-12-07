import queue
import threading
import time
from embedded.coffee_api.api import add_purchase
from embedded.hx711 import HX711
import multiprocessing

DT_PIN = 27
SCK_PIN = 17


def dispense_task(measure_coffee_queue: multiprocessing.Queue, recognize_customer_event_flag, coffee_container, turn_on_motor_event_flag, register_customer_event_flag):
    hx = HX711(DT_PIN, SCK_PIN)
    print("Setting up load cell")
    referenceUnit =  401339.77777777775/211
    hx.set_reference_unit(referenceUnit)
    hx.reset()
    hx.tare()

    print("Calibration complete")
    while True:
        
        measure_coffee_request = measure_coffee_queue.get()
        print(f"Received request {measure_coffee_request}")

        container_id = measure_coffee_request["container_id"]
        customer_id = measure_coffee_request["customer_id"]
        coffee_id = measure_coffee_request["coffee_id"]
        with coffee_container.get_lock():
            print(f"Updated container to dispense to {container_id}")
            coffee_container.value = container_id
        
        requested_coffee_weight = measure_coffee_request["weight"]
        turn_on_motor_event_flag.set()

        weight = 0
        while weight <= requested_coffee_weight: 
            weight = int(hx.get_weight(5))
            print(f"Weight = {weight}")
            hx.power_down()
            hx.power_up()
            time.sleep(0.1)
        
        time.sleep(2)
        weight = int(hx.get_weight(5))
        print(f"Finished dispense of coffee {coffee_id} with weight : {weight}")

        turn_on_motor_event_flag.clear()
        if customer_id == -1:
            register_customer_event_flag.set()
        else:
            print("Adding purchase to the customer")
            add_purchase(customer_id, weight, coffee_id)
            recognize_customer_event_flag.set()
        


        

