import time

import serial
from embedded.arduino import send_to_arduino, initialize_arduino, arduino

initialize_arduino()

send_to_arduino("UPDATE:STATE:IDLE")
time.sleep(10)
send_to_arduino("UPDATE:STATE:TALKING")
time.sleep(5)
send_to_arduino("UPDATE:STATE:DISPENSING")
time.sleep(5)

for i in range(0, 100, 10):
    send_to_arduino(f"UPDATE:WEIGHT:{i}")
    time.sleep(0.5)
