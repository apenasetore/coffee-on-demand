import multiprocessing
import RPi.GPIO as GPIO
import time


#PINS FOR MOTOR 1
M1_DIR_PIN = 23 
M1_STEP_PIN = 24 
M1_MS1_PIN = 21 
M1_MS2_PIN = 20 
M1_MS3_PIN = 16 

#PINS FOR MOTOR 2
M2_DIR_PIN = 1 
M2_STEP_PIN = 2 
M2_MS1_PIN = 3 
M2_MS2_PIN = 4 
M2_MS3_PIN = 5 

#PINS FOR MOTOR 3
M3_DIR_PIN = 6
M3_STEP_PIN = 7 
M3_MS1_PIN = 8 
M3_MS2_PIN = 9 
M3_MS3_PIN = 10

#PINS FOR MOTOR 4
M4_DIR_PIN = 11 
M4_STEP_PIN = 12 
M4_MS1_PIN = 13
M4_MS2_PIN = 14 
M4_MS3_PIN = 15 

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(M1_DIR_PIN, GPIO.OUT)
    GPIO.setup(M1_STEP_PIN, GPIO.OUT)
    GPIO.setup(M1_MS1_PIN, GPIO.OUT)
    GPIO.setup(M1_MS2_PIN, GPIO.OUT)
    GPIO.setup(M1_MS3_PIN, GPIO.OUT)

    # GPIO.setup(M2_DIR_PIN, GPIO.OUT)
    # GPIO.setup(M2_STEP_PIN, GPIO.OUT)
    # GPIO.setup(M2_MS1_PIN, GPIO.OUT)
    # GPIO.setup(M2_MS2_PIN, GPIO.OUT)
    # GPIO.setup(M2_MS3_PIN, GPIO.OUT)

    # GPIO.setup(M3_DIR_PIN, GPIO.OUT)
    # GPIO.setup(M3_STEP_PIN, GPIO.OUT)
    # GPIO.setup(M3_MS1_PIN, GPIO.OUT)
    # GPIO.setup(M3_MS2_PIN, GPIO.OUT)
    # GPIO.setup(M3_MS3_PIN, GPIO.OUT)

    # GPIO.setup(M4_DIR_PIN, GPIO.OUT)
    # GPIO.setup(M4_STEP_PIN, GPIO.OUT)
    # GPIO.setup(M4_MS1_PIN, GPIO.OUT)
    # GPIO.setup(M4_MS2_PIN, GPIO.OUT)
    # GPIO.setup(M4_MS3_PIN, GPIO.OUT)

    GPIO.output(M1_DIR_PIN, GPIO.HIGH)
    GPIO.output(M1_MS1_PIN, GPIO.LOW)
    GPIO.output(M1_MS2_PIN, GPIO.HIGH)
    GPIO.output(M1_MS3_PIN, GPIO.LOW)

    # GPIO.output(M2_DIR_PIN, GPIO.HIGH)
    # GPIO.output(M2_MS1_PIN, GPIO.LOW)
    # GPIO.output(M2_MS2_PIN, GPIO.HIGH)
    # GPIO.output(M2_MS3_PIN, GPIO.LOW)

    # GPIO.output(M3_DIR_PIN, GPIO.HIGH)
    # GPIO.output(M3_MS1_PIN, GPIO.LOW)
    # GPIO.output(M3_MS2_PIN, GPIO.HIGH)
    # GPIO.output(M3_MS3_PIN, GPIO.LOW)

    # GPIO.output(M4_DIR_PIN, GPIO.HIGH)
    # GPIO.output(M4_MS1_PIN, GPIO.LOW)
    # GPIO.output(M4_MS2_PIN, GPIO.HIGH)
    # GPIO.output(M4_MS3_PIN, GPIO.LOW)

def motor_task(turn_on_motor_event_flag, coffee_container):
    setup()

    coffee_1 = {"DIR_PIN": M1_DIR_PIN, "STEP_PIN": M1_STEP_PIN, "MS1_PIN": M1_MS1_PIN, "MS2_PIN": M1_MS2_PIN, "MS3_PIN": M1_MS3_PIN}
    coffee_2 = {"DIR_PIN": M2_DIR_PIN, "STEP_PIN": M2_STEP_PIN, "MS1_PIN": M2_MS1_PIN, "MS2_PIN": M2_MS2_PIN, "MS3_PIN": M2_MS3_PIN}
    coffee_3 = {"DIR_PIN": M3_DIR_PIN, "STEP_PIN": M3_STEP_PIN, "MS1_PIN": M3_MS1_PIN, "MS2_PIN": M3_MS2_PIN, "MS3_PIN": M3_MS3_PIN}
    coffee_4 = {"DIR_PIN": M4_DIR_PIN, "STEP_PIN": M4_STEP_PIN, "MS1_PIN": M4_MS1_PIN, "MS2_PIN": M4_MS2_PIN, "MS3_PIN": M4_MS3_PIN}

    coffee_configs = [coffee_1, coffee_2, coffee_3, coffee_4]
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

            dir_pin = coffee_configs[coffee_index]["DIR_PIN"]
            step_pin = coffee_configs[coffee_index]["STEP_PIN"]

        if turn_on_motor_event_flag.is_set():
            print("Forward")
            for i in range(400):
                if not turn_on_motor_event_flag.is_set():
                    break
                GPIO.output(dir_pin, GPIO.HIGH)
                GPIO.output(step_pin, GPIO.HIGH)
                time.sleep(delay)
                GPIO.output(step_pin, GPIO.LOW)
                time.sleep(delay)

        if turn_on_motor_event_flag.is_set():
            print("Backwards")
            for i in range(300):
                if not turn_on_motor_event_flag.is_set():
                    break

                GPIO.output(dir_pin, GPIO.LOW)
                GPIO.output(step_pin, GPIO.HIGH)
                time.sleep(delay)
                GPIO.output(step_pin, GPIO.LOW)
                time.sleep(delay)

