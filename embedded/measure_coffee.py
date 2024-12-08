import queue
import threading
import time
from embedded.coffee_api.api import add_purchase
from embedded.gpt import play_audio
from embedded.hx711 import HX711
import multiprocessing
from embedded.arduino import send_to_arduino

DT_PIN = 27
SCK_PIN = 17


def dispense_task(measure_coffee_queue: multiprocessing.Queue, purchase_queue: multiprocessing.Queue, recognize_customer_event_flag, coffee_container, turn_on_motor_event_flag, register_customer_event_flag,turn_on_cup_sensor):
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
        
        send_to_arduino("UPDATE:STATE:DISPENSING")
        requested_coffee_weight = measure_coffee_request["weight"]
        turn_on_motor_event_flag.set()
        turn_on_cup_sensor.set()

        weight = 0
        last_reading = weight
        weight_reduction = False
        while weight <= requested_coffee_weight or weight_reduction: 
            weight = int(hx.get_weight(5))
            if weight < 0:
                weight = 0

            send_to_arduino(f"UPDATE:WEIGHT:{weight}")
            print(f"Weight = {weight}")
            if last_reading > weight + 2: #2 gramas de erro
                weight_reduction = True
                print("Weight has reduced, stopping motors.")
                turn_on_motor_event_flag.clear()
                play_audio("We have detected a weight reduction, please put back the coffee container.")
            elif weight_reduction:
                play_audio("Resuming dispensing.")
                weight_reduction = False
                turn_on_motor_event_flag.set()

            if not weight_reduction:
                last_reading = weight
            hx.power_down()
            hx.power_up()
        print("Got out")
        
        time.sleep(2)
        weight = int(hx.get_weight(5))
        print(f"Finished dispense of coffee {coffee_id} with weight : {weight}")
        send_to_arduino(f"UPDATE:WEIGHT:{weight}")

        
        turn_on_motor_event_flag.clear()
        turn_on_cup_sensor.clear()
        if customer_id == -1:
            purchase_queue.put(
                {"weight": weight, "coffee_id": coffee_id}
            )
            register_customer_event_flag.set()
        else:
            print("Adding purchase to the customer")
            add_purchase(customer_id, weight, coffee_id)
            recognize_customer_event_flag.set()
        


        

