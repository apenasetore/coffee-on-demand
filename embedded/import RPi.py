import RPi.GPIO as GPIO
import time

# Configuração dos pinos
DIR_PIN = 20  # Pino de direção
STEP_PIN = 21  # Pino de passo

# Configuração dos GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)

# Definir a direção do motor (HIGH = horário, LOW = anti-horário)
GPIO.output(DIR_PIN, GPIO.HIGH)

try:
    while True:
        # Gera um pulso de passo
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(0.001)  # Delay entre os pulsos (ajusta a velocidade)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(0.001)

except KeyboardInterrupt:
    print("Parando o motor...")

finally:
    GPIO.cleanup()  # Limpa as configurações dos GPIO