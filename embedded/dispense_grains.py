import RPi.GPIO as GPIO
import time

# Configuração dos pinos GPIO
DIR_PIN = 2  # Pino GPIO para direção
STEP_PIN = 3  # Pino GPIO para passos
MS1_PIN = 22 
MS2_PIN = 27 
MS3_PIN = 17 

# Configuração dos parâmetros do motor
STEPS_PER_REV = 200  # Passos por revolução (1.8° por passo no modo full-step)
SPEED = 0.001  # Intervalo entre os passos (ajuste para velocidade)

# Configuração inicial dos pinos
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(MS1_PIN, GPIO.OUT)
GPIO.setup(MS2_PIN, GPIO.OUT)
GPIO.setup(MS3_PIN, GPIO.OUT)

GPIO.output(DIR_PIN, GPIO.HIGH)
GPIO.output(MS1_PIN, GPIO.LOW)
GPIO.output(MS2_PIN, GPIO.HIGH)
GPIO.output(MS3_PIN, GPIO.LOW)

velocity = 30
delay = 500000 / velocity

while True:
    for i in range(400):
        GPIO.output(DIR_PIN, GPIO.HIGH)
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)

    for i in range(300):
        GPIO.output(DIR_PIN, GPIO.LOW)
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
