import serial
import time

arduino = serial.Serial('COM16', 9600, timeout=1)

time.sleep(2)

print("Waiting for fingerprint...")

while True:
    data = arduino.readline().decode().strip()

    if data:
        print(data)