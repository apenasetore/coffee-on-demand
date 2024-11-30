import multiprocessing
import RPi.GPIO as GPIO
import time


#PINS
M1_STEP_PIN = 3 
M2_STEP_PIN = 2
M3_STEP_PIN = 16
M4_STEP_PIN = 20
DIR_PIN = 21 
MS1_PIN = 26 
MS2_PIN = 19
MS3_PIN = 13 


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(M1_STEP_PIN, GPIO.OUT)
    GPIO.setup(M2_STEP_PIN, GPIO.OUT)
    GPIO.setup(M3_STEP_PIN, GPIO.OUT)
    GPIO.setup(M4_STEP_PIN, GPIO.OUT)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(MS1_PIN, GPIO.OUT)
    GPIO.setup(MS2_PIN, GPIO.OUT)
    GPIO.setup(MS3_PIN, GPIO.OUT)

    GPIO.output(DIR_PIN, GPIO.HIGH)
    GPIO.output(MS1_PIN, GPIO.LOW)
    GPIO.output(MS2_PIN, GPIO.HIGH)
    GPIO.output(MS3_PIN, GPIO.LOW)


def motor_task(turn_on_motor_event_flag, coffee_container):
    setup()

    coffee_configs = [M1_STEP_PIN, M2_STEP_PIN, M3_STEP_PIN, M4_STEP_PIN]
    delay = 0.0003

    while True:
        print("Waiting for event flag")
        while not turn_on_motor_event_flag.is_set():
            pass

        with coffee_container.get_lock():
            print(f"Loading config of {coffee_container.value=}")
            coffee_index = coffee_container.value - 1
            
            if coffee_index > 3 or coffee_index < 0:
                coffee_index = 0

            step_pin = coffee_configs[coffee_index]

        if turn_on_motor_event_flag.is_set():
            print("Forward")
            for i in range(400):
                if not turn_on_motor_event_flag.is_set():
                    break
                GPIO.output(DIR_PIN, GPIO.HIGH)
                GPIO.output(step_pin, GPIO.HIGH)
                time.sleep(delay)
                GPIO.output(step_pin, GPIO.LOW)
                time.sleep(delay)

        if turn_on_motor_event_flag.is_set():
            print("Backwards")
            for i in range(300):
                if not turn_on_motor_event_flag.is_set():
                    break

                GPIO.output(DIR_PIN, GPIO.LOW)
                GPIO.output(step_pin, GPIO.HIGH)
                time.sleep(delay)
                GPIO.output(step_pin, GPIO.LOW)
                time.sleep(delay)

