import RPi.GPIO as GPIO
import time

# Configuração dos pinos GPIO
DIR_PIN = 12  # Pino para definir a direção
M1_STEP_PIN = 5  # Pino para enviar os pulsos de passo
M2_STEP_PIN = 6
M3_STEP_PIN = 13
M4_STEP_PIN = 26

# Configuração dos GPIOs
GPIO.setmode(GPIO.BCM)

GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(M1_STEP_PIN, GPIO.OUT)
GPIO.setup(M2_STEP_PIN, GPIO.OUT)
GPIO.setup(M3_STEP_PIN, GPIO.OUT)
GPIO.setup(M4_STEP_PIN, GPIO.OUT)


GPIO.output(M1_STEP_PIN, GPIO.LOW)
GPIO.output(M2_STEP_PIN, GPIO.LOW)
GPIO.output(M3_STEP_PIN, GPIO.LOW)
GPIO.output(M4_STEP_PIN, GPIO.LOW)

# Configuração da direção (True para frente, False para trás)
 # Ajuste para frente

# Fazendo o motor girar (um pequeno "forzinho")
try:
    while True:

        GPIO.output(DIR_PIN, GPIO.HIGH)

        for _ in range(300):  # 200 passos (ajuste conforme necessário)
            GPIO.output(M2_STEP_PIN, GPIO.HIGH)
            time.sleep(0.0005)  # Tempo HIGH (ajuste para controle de velocidade)
            GPIO.output(M2_STEP_PIN, GPIO.LOW)
            time.sleep(0.0005)  # Tempo LOW
            print("Rotating")


        GPIO.output(DIR_PIN, GPIO.LOW) 

        for _ in range(150):  # 200 passos (ajuste conforme necessário)
            GPIO.output(M2_STEP_PIN, GPIO.HIGH)
            time.sleep(0.0005)  # Tempo HIGH (ajuste para controle de velocidade)
            GPIO.output(M2_STEP_PIN, GPIO.LOW)
            time.sleep(0.0005)  # Tempo LOW
            print("Rotating")
            
except KeyboardInterrupt:
    print("Parando...")
finally:
    GPIO.output(M1_STEP_PIN, GPIO.LOW)
    GPIO.output(M2_STEP_PIN, GPIO.LOW)
    GPIO.output(M3_STEP_PIN, GPIO.LOW)
    GPIO.output(M4_STEP_PIN, GPIO.LOW)
