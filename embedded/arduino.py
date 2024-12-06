import serial.tools.list_ports
import serial


def get_arduino():
    """
    Finds the Arduino USB port by checking available COM ports.
    Returns:
        str: The port name (e.g., 'COM3' or '/dev/ttyUSB0') if found, otherwise None.
    """
    portas = serial.tools.list_ports.comports()
    for porta in portas:
        if porta.manufacturer and "Arduino" in porta.manufacturer:
            return porta.device
    return None


def send_to_arduino(payload: str):
    """
    Sends a string payload to the Arduino via serial communication.
    Args:
        payload (str): The data to send to the Arduino.
    """
    port = get_arduino()
    if not port:
        raise ValueError("Arduino device not found.")
    
    try:
        with serial.Serial(port, 9600, timeout=2) as arduino:  # Correct usage of Serial class
            payload = payload + "\n"
            arduino.write(payload.encode())
            print("Payload sent successfully.")
    except serial.SerialException as e:
        print(f"Failed to send payload: {e}")


def load_arduino():
    """
    Initializes communication with the Arduino.
    """
    port = get_arduino()
    if not port:
        raise ValueError("Arduino device not found.")
    
    try:
        with serial.Serial(port, 9600, timeout=2) as arduino:  # Correct usage of Serial class
            print("Arduino connected successfully.")
    except serial.SerialException as e:
        print(f"Failed to connect to Arduino: {e}")
