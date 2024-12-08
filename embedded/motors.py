import multiprocessing
import RPi.GPIO as GPIO
import time

from embedded.gpt import play_audio

# PINS
M1_STEP_PIN = 12
M2_STEP_PIN = 6
M3_STEP_PIN = 13
M4_STEP_PIN = 26
DIR_PIN = 5

DELAY = 0.001
BIG_DELAY = 0.008

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


def motor_task(turn_on_motor_event_flag, removed_coffee_container, slow_mode_event_flag, coffee_container):
    setup()

    coffee_configs = [M1_STEP_PIN, M2_STEP_PIN, M3_STEP_PIN, M4_STEP_PIN]
    delay = DELAY
    positive_gain = 100
    negative_gain = 50

    try:
        while True:
            while not turn_on_motor_event_flag.is_set():
                pass

            with coffee_container.get_lock():
                print(f"Loading config of {coffee_container.value=}")
                coffee_index = coffee_container.value

                if coffee_index > 3 or coffee_index < 0:
                    coffee_index = 0

                step_pin = coffee_configs[coffee_index]

            if turn_on_motor_event_flag.is_set():
                #print(f"Forward {step_pin} with delay {delay}")
                GPIO.output(DIR_PIN, GPIO.HIGH)
                for _ in range(positive_gain):
                    if not turn_on_motor_event_flag.is_set():
                        break
                    if removed_coffee_container.is_set():
                        print("Removed coffee container")
                        break
                    if slow_mode_event_flag.is_set():
                        delay = BIG_DELAY
                    GPIO.output(step_pin, GPIO.HIGH)
                    time.sleep(delay) 
                    GPIO.output(step_pin, GPIO.LOW)
                    time.sleep(delay)

            if turn_on_motor_event_flag.is_set():
                #print("Backwards")
                GPIO.output(DIR_PIN, GPIO.LOW) 
                for _ in range(negative_gain):
                    if not turn_on_motor_event_flag.is_set():
                        break
                    if removed_coffee_container.is_set():
                        print("Removed coffee container")
                        break
                    if slow_mode_event_flag.is_set():
                        delay = BIG_DELAY
                    GPIO.output(step_pin, GPIO.HIGH)
                    time.sleep(delay) 
                    GPIO.output(step_pin, GPIO.LOW)
                    time.sleep(delay)

    except KeyboardInterrupt:
        print("Cleaning motors")
        clean_motors()