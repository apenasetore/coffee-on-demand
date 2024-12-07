import time
import RPi.GPIO as GPIO
from threading import Event

# Define the GPIO pin connected to the infrared sensor
IR_SENSOR_PIN = 22

def setup():
    """
    Set up the GPIO pin for the infrared sensor.
    """
    GPIO.setmode(GPIO.BCM)  # Use BCM numbering
    GPIO.setup(IR_SENSOR_PIN, GPIO.IN)

def read_sensor():
    """
    Read the infrared sensor's state.
    Returns:
        bool: True if the sensor detects an object, False otherwise.
    """
    return GPIO.input(IR_SENSOR_PIN) == GPIO.HIGH

def read_sensor_thread():
    """
    Continuously check the sensor state and signal when the coffee container is removed.
    Args:
        turn_on_cup_sensor (Event): Event to indicate when the sensor monitoring should start.
        removed_coffee_container (Event): Event to indicate when the coffee container has been removed.
    """
    while True:
        value = read_sensor()
        print(f"Sensor state: {value}")
        time.sleep(0.5)  # Delay between readings

if __name__ == "__main__":
    read_sensor_thread()