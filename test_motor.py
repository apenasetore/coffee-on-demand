import RPi.GPIO as GPIO
import time

# Configuração dos pinos GPIO
DIR_PIN = 5  # Pino para definir a direção
STEP_PIN = 6  # Pino para enviar os pulsos de passo

# Configuração dos GPIOs
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)

# Configuração da direção (True para frente, False para trás)
 # Ajuste para frente

# Fazendo o motor girar (um pequeno "forzinho")
try:
    while True:

        GPIO.output(DIR_PIN, GPIO.HIGH)

        for _ in range(100):  # 200 passos (ajuste conforme necessário)
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(0.001)  # Tempo HIGH (ajuste para controle de velocidade)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.001)  # Tempo LOW
            print("Rotating")


        GPIO.output(DIR_PIN, GPIO.LOW) 

        for _ in range(50):  # 200 passos (ajuste conforme necessário)
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(0.001)  # Tempo HIGH (ajuste para controle de velocidade)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.001)  # Tempo LOW
            print("Rotating")
            
except KeyboardInterrupt:
    print("Parando...")
finally:
    GPIO.output(STEP_PIN, GPIO.LOW)  # Limpa a configuração dos pinos GPIO
