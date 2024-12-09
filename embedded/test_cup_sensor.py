import time
import RPi.GPIO as GPIO
from threading import Event

IR_SENSOR_PIN = 22

def setup():
    GPIO.setmode(GPIO.BCM) 
    GPIO.setup(IR_SENSOR_PIN, GPIO.IN)

def read_sensor():
    return GPIO.input(IR_SENSOR_PIN) == GPIO.HIGH

def read_sensor_thread():
    while True:
        value = not read_sensor()
        print(f"Sensor state: {value}")
        time.sleep(0.2) 

if __name__ == "__main__":
    setup()
    read_sensor_thread()