import multiprocessing
import RPi.GPIO as GPIO
import time

from embedded.gpt import play_audio

# PINS
M1_STEP_PIN = 5
M2_STEP_PIN = 6
M3_STEP_PIN = 13
M4_STEP_PIN = 26
DIR_PIN = 12


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(M1_STEP_PIN, GPIO.OUT)
    GPIO.setup(M2_STEP_PIN, GPIO.OUT)
    GPIO.setup(M3_STEP_PIN, GPIO.OUT)
    GPIO.setup(M4_STEP_PIN, GPIO.OUT)
    
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.output(DIR_PIN, GPIO.LOW)

    clean_motors()

def clean_motors():
    GPIO.output(M1_STEP_PIN, GPIO.LOW)
    GPIO.output(M2_STEP_PIN, GPIO.LOW)
    GPIO.output(M3_STEP_PIN, GPIO.LOW)
    GPIO.output(M4_STEP_PIN, GPIO.LOW)
    print("Cleaned motors")


def motor_task(turn_on_motor_event_flag, turn_on_cup_sensor, removed_coffee_container, coffee_container):
    setup()

    coffee_configs = [M1_STEP_PIN, M2_STEP_PIN, M3_STEP_PIN, M4_STEP_PIN]
    delay = 0.0005

    try:
        while True:
            print("Waiting for event flag")
            while not turn_on_motor_event_flag.is_set():
                pass


            with coffee_container.get_lock():
                print(f"Loading config of {coffee_container.value=}")
                coffee_index = coffee_container.value

                if coffee_index > 3 or coffee_index < 0:
                    coffee_index = 0

                step_pin = coffee_configs[coffee_index]

            turn_on_cup_sensor.set()

            if turn_on_motor_event_flag.is_set():
                print(f"Forward {step_pin}")
                for i in range(400):
                    if not turn_on_motor_event_flag.is_set():
                        break
                    if removed_coffee_container.is_set():
                        print("Removed coffee container")
                        break
                    GPIO.output(DIR_PIN, GPIO.LOW)
                    GPIO.output(step_pin, GPIO.HIGH)
                    time.sleep(delay)
                    GPIO.output(step_pin, GPIO.LOW)
                    time.sleep(delay)

            time.sleep(0.1)

            if turn_on_motor_event_flag.is_set():
                print("Backwards")
                for i in range(300):
                    if not turn_on_motor_event_flag.is_set():
                        break
                    
                    if removed_coffee_container.is_set():
                        print("Removed coffee container")
                        break

                    GPIO.output(DIR_PIN, GPIO.HIGH)
                    GPIO.output(step_pin, GPIO.HIGH)
                    time.sleep(delay)
                    GPIO.output(step_pin, GPIO.LOW)
                    time.sleep(delay)

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Cleaning motors")
        clean_motors()