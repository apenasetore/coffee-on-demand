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

motors = [M1_STEP_PIN, M2_STEP_PIN, M3_STEP_PIN,M4_STEP_PIN]

try:
    while True:

        for motor in motors:

            for i in range(4):
                GPIO.output(DIR_PIN, GPIO.HIGH)

                for _ in range(200):  # 200 passos (ajuste conforme necessário)
                    GPIO.output(motor, GPIO.HIGH)
                    time.sleep(0.001)  # Tempo HIGH (ajuste para controle de velocidade)
                    GPIO.output(motor, GPIO.LOW)
                    time.sleep(0.001)  # Tempo LOW
                    print("Rotating")


                GPIO.output(DIR_PIN, GPIO.LOW) 

                for _ in range(100):  # 200 passos (ajuste conforme necessário)
                    GPIO.output(motor, GPIO.HIGH)
                    time.sleep(0.001)  # Tempo HIGH (ajuste para controle de velocidade)
                    GPIO.output(motor, GPIO.LOW)
                    time.sleep(0.001)  # Tempo LOW
                    print("Rotating")
            
            time.sleep(0.5)
            
except KeyboardInterrupt:
    print("Parando...")
finally:
    GPIO.output(M1_STEP_PIN, GPIO.LOW)
    GPIO.output(M2_STEP_PIN, GPIO.LOW)
    GPIO.output(M3_STEP_PIN, GPIO.LOW)
    GPIO.output(M4_STEP_PIN, GPIO.LOW)
