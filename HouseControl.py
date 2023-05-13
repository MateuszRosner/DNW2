import time
import RPi._GPIO as GPIO

from time import sleep

from config import config, TXDEN_1, TXDEN_2, BAUD_38400



ser1 = config(dev="/dev/ttySC0", Baudrate=BAUD_38400)
ser2 = config(dev="/dev/ttySC1", Baudrate=BAUD_38400)

data = "Test data \r\n"

print("Initialize...")

data_frame = [1,3,0,0,0,0,2,2]
data_bytes = bytearray(data_frame)

while True:
    GPIO.output(TXDEN_1, GPIO.LOW)     # transmitter

    #ser1.Uart_SendString(data)
    #sleep(0.02)
    ser1.Uart_SendByte(data_bytes)

    GPIO.output(TXDEN_1, GPIO.HIGH)    # reciver

    data = ser1.Uart_ReceiveString(8)
    print(data)

    sleep(1)