#!/usr/bin/python
# -*- coding:utf-8 -*-

import serial
import RPi._GPIO as GPIO

TXDEN_1 = 27
TXDEN_2 = 22

BAUD_38400 = 38400

# dev = "/dev/ttySC0"

class config(object):
    def __init__(self, Baudrate = 115200, dev = "/dev/ttyS0"):
        print (dev)
        self.dev = dev
        self.serial = serial.Serial(self.dev, Baudrate)
        self.serial.timeout = 1
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TXDEN_1, GPIO.OUT)
        GPIO.setup(TXDEN_2, GPIO.OUT)

        GPIO.output(TXDEN_1, GPIO.HIGH)
        GPIO.output(TXDEN_2, GPIO.HIGH)

        self.FlushBuffer()
        
    def Uart_SendByte(self, value): 
        self.serial.write(value) 
    
    def Uart_SendString(self, value): 
        self.serial.write(value.encode('ascii'))

    def Uart_ReceiveByte(self): 
        return self.serial.read(1).decode("utf-8")

    def Uart_ReceiveString(self, value): 
        data = self.serial.read(value)
        return bytearray(data)#.decode("utf-8")
        
    def Uart_Set_Baudrate(self, Baudrate):
         self.serial = serial.Serial(self.dev, Baudrate)

    def Uart_SendData(self, data):
        for x in range(len(data)):
            self.Uart_SendByte(chr(data[x]))

    def FlushBuffer(self):
        self.serial.flush()
    
    
        
         
         
         