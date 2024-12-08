import time
import serial.tools.list_ports
import serial


arduino = None


def initialize_arduino():
    global arduino
    arduino_port = None
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.manufacturer and "Arduino" in port.manufacturer:
            arduino_port = port.device

    if not arduino_port:
        raise ValueError("Arduino device not found.")

    print(f"Conectando ao Arduino na porta: {port}")
    arduino = serial.Serial(arduino_port, 9600, timeout=2)


def send_to_arduino(payload: str):
    """
    Sends a string payload to the Arduino via serial communication and prints the response.
    """
    try:
        time.sleep(0.2)  # Aguarda a inicialização do Arduino
        payload = payload + "\n"  # Adiciona o caractere de término
        print(f"Enviando: {payload.encode()}")

        arduino.write(payload.encode())  # Envia os dados)
    except serial.SerialException as e:
        print(f"Erro na comunicação com o Arduino: {e}")
