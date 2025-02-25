import time
from embedded.coffee_api.api import add_purchase
import embedded.gpt_audio_preview as gpt
from embedded.hx711 import HX711
import multiprocessing
from embedded.arduino import send_to_arduino
from embedded.coffee_api.api import (
    add_notification
)

DT_PIN = 27
SCK_PIN = 17


def dispense_task(
    measure_coffee_queue: multiprocessing.Queue,
    purchase_queue: multiprocessing.Queue,
    recognize_customer_event_flag,
    coffee_container,
    turn_on_motor_event_flag,
    slow_mode_event_flag,
    register_customer_event_flag,
    turn_on_cup_sensor,
    removed_coffee_container,
):
    hx = HX711(DT_PIN, SCK_PIN)
    print("Setting up load cell")
    referenceUnit = 401339.77777777775 / 211
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

        turn_on_cup_sensor.set()
        time.sleep(1)

        while removed_coffee_container.is_set():
            gpt.play_audio("Please put a coffee container in place!")
            time.sleep(3)

        cup_in_place = 0
        while not removed_coffee_container.is_set() and cup_in_place < 10:
            cup_in_place += 1

        referenceUnit = 401339.77777777775 / 211
        hx.set_reference_unit(referenceUnit)
        hx.reset()
        hx.tare()

        hx.power_down()
        hx.power_up()

        print("Staring to dispense")

        send_to_arduino("UPDATE:WEIGHT:0")
        send_to_arduino("UPDATE:STATE:DISPENSING")
        requested_coffee_weight = measure_coffee_request["weight"]
        turn_on_motor_event_flag.set()

        weight = 0
        last_reading = weight
        weight_reduction = False
        weight_reduction_count = 0
        machine_stuck = 0
        while weight < requested_coffee_weight or weight_reduction:
            weight = int(hx.get_weight(3))

            if weight >= requested_coffee_weight:
                print("Weight has achieved target value, stopping motors.")
                turn_on_motor_event_flag.clear()

            if weight < 0:
                weight = 0

            send_to_arduino(f"UPDATE:WEIGHT:{weight}")


            # if requested_coffee_weight - weight <= 1:
            #     turn_on_motor_event_flag.clear()
            #     print("Activating slow mode")

            #     while weight < requested_coffee_weight or weight_reduction:

            #         if last_reading > weight + 2:
            #             weight_reduction = True
            #             print("Weight has reduced, stopping motors.")
            #             turn_on_motor_event_flag.clear()
            #             gpt.play_audio(
            #                 "We have detected a weight reduction, please put back the coffee container."
            #             )
            #         elif weight_reduction:
            #             gpt.play_audio("Resuming dispensing.")
            #             weight_reduction = False
            #             turn_on_motor_event_flag.set()

            #         if not weight_reduction:
            #             last_reading = weight

            #         print(f"Weight = {weight}")
            #         send_to_arduino(f"UPDATE:WEIGHT:{weight}")

            #         time.sleep(3)

            #         turn_on_motor_event_flag.set()
            #         time.sleep(0.12)
            #         turn_on_motor_event_flag.clear()

            #         hx.power_down()
            #         hx.power_up()
            #         weight = int(hx.get_weight(3))

            #         print(f"Weight = {weight}")
            #         send_to_arduino(f"UPDATE:WEIGHT:{weight}")

            if last_reading > weight + 2:
                weight_reduction = True
                weight_reduction_count += 1

                if weight_reduction_count >= 5:
                    gpt.play_audio("I think ypu are trying to steal coffee, notifying manager.")
                    add_notification("Coffee has been stolen!")
                    while True:
                        time.sleep(10)
                        gpt.play_audio("The machine has some problem, I'm in maintenance waiting for the manager")

                print("Weight has reduced, stopping motors.")
                turn_on_motor_event_flag.clear()
                gpt.play_audio(
                    "We have detected a weight reduction, please put back the coffee container, otherwise I will notify the manager."
                )
            elif weight_reduction:
                gpt.play_audio("Resuming dispensing.")
                send_to_arduino(f"UPDATE:STATE:DISPENSING")
                weight_reduction = False
                turn_on_motor_event_flag.set()

            if not weight_reduction:
                weight_reduction_count = 0
                if weight != last_reading:
                    machine_stuck = 0
                    last_reading = weight
                else:
                    machine_stuck += 1
                    if machine_stuck >= 50:
                        turn_on_motor_event_flag.clear()
                        turn_on_cup_sensor.clear()
                        gpt.play_audio("Oh! I noticed that maybe the machine is stuck. Sorry for the inconvenience. I will send a notification to the manager.")
                        add_notification("Machine stuck")
                        while True:
                            time.sleep(10)
                            gpt.play_audio("The machine has some problem, I'm in maintenance")

        turn_on_motor_event_flag.clear()
        turn_on_cup_sensor.clear()
        slow_mode_event_flag.clear()

        final_weight = weight
        print(f"Finished dispense of coffee {coffee_id} with weight : {final_weight}")
        # send_to_arduino(f"UPDATE:WEIGHT:{final_weight}")

        time.sleep(3)

        while weight > -2:  # 2 gramas de erro
            gpt.play_audio("Please remove your coffee!")
            time.sleep(3)
            weight = int(hx.get_weight(3))

        if customer_id == -1:
            purchase_queue.put({"weight": final_weight, "coffee_id": coffee_id})
        else:
            gpt.play_audio("I've finished dispensing. Thank you!")
            print("Adding purchase to the customer")
            add_purchase(customer_id, final_weight, coffee_id)
            recognize_customer_event_flag.set()
