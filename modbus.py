import threading
import serial
import RPi._GPIO as GPIO
import configparser
import time
import copy

import modbusCommands as mC

from modbusFrame import ModbusFrame
from datetime import datetime

TXDEN_1 = 27
TXDEN_2 = 22

BAUD_38400 = 38400
BAUD_9600  = 9600

    
class Modbus():
    def __init__(self, baudrate=9600, dev="/dev/ttySC1", crcControl=True, dataLen=8):
         # --------------- config file reading    ---------------
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.ser=serial.Serial(
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0.1)

        self.dev = dev
        self.ser.port = self.dev

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TXDEN_2, GPIO.OUT)
        GPIO.output(TXDEN_2, GPIO.HIGH)

        try:
            self.ser.open() 
        except serial.SerialException:
            print("[ERROR] Can't open serial port")

        self.frame = ModbusFrame(4)
        self.rec_data_len = dataLen
        self.crc_control = crcControl
    
    def send_frame(self, frame):
        
        if self.ser.isOpen():
            frame.calcCRC()
            GPIO.output(TXDEN_2, GPIO.LOW)     # transmitter
            time.sleep(0.006)
            frame = bytearray(frame)
            self.ser.write(frame)
            time.sleep(0.004)
            GPIO.output(TXDEN_2, GPIO.HIGH)    # reciver

    def read_data(self, dataLen=7):
        if self.ser.isOpen() == True:
            self.frame.data.clear()
            data = self.ser.read(dataLen)
            data = bytearray(data)

            if len(data) < dataLen:
                print(data)
                self.frame.clear()
                self.ser.flush()
                return False
            else:
                self.frame.address = (data[0])
                self.frame.command = (data[1])
                self.frame.data.append((data[2]))
                self.frame.data.append((data[3]))
                self.frame.data.append((data[4]))

                self.frame.CRC = (data[5] & 0xFF) | (data[6] << 8)

                print(self.frame)

                # check CRC
                if self.crc_control == True:
                    CRC = self.frame.CRC
                    self.frame.calcCRC()

                    if CRC != self.frame.CRC:
                        print("[WARNING] CRC error modbus")
                        self.frame.clear()
                        self.ser.flush()
                        return False
                        
        return True
    
    def read_coil_data(self, dataLen=6):
        if self.ser.isOpen() == True:
            self.frame.data.clear()
            data = self.ser.read(dataLen)
            data = bytearray(data)

            if len(data) < dataLen:
                print(data)
                self.frame.clear()
                self.ser.flush()
                return False
            else:
                self.frame.address = (data[0])
                self.frame.command = (data[1])
                self.frame.data.append((data[2]))
                self.frame.data.append((data[3]))

                self.frame.CRC = (data[4] & 0xFF) | (data[5] << 8)

                print(self.frame)

                # check CRC
                if self.crc_control == True:
                    CRC = self.frame.CRC
                    self.frame.calcCRC()

                    if CRC != self.frame.CRC:
                        print("[WARNING] CRC error modbus")
                        self.frame.clear()
                        self.ser.flush()
                        return False
                        
        return True

    def Test(self):
        frame = ModbusFrame(4)
        frame.address = 0x01
        frame.command = 0x03
        frame.data[0] = 0x00
        frame.data[1] = mC.RTD_NET_SETPOINT
        frame.data[2] = 0x00
        frame.data[3] = 0x01
        
        self.send_frame(frame)

        if self.read_data() == True:
            print("Modbus alive")
            frame.data[1] = mC.RTD_NET_MODE
            self.send_frame(frame)
            self.read_data()
        else:
            print("Modbus is dead")

    def set_ac_params(self, resources):
        frame = ModbusFrame(4)
        frame.address = 0x01
        frame.command = mC.MODBUS_WRITE
        frame.data[0] = 0x00
        frame.data[1] = mC.RTD_NET_SETPOINT
        frame.data[2] = 0x00
        frame.data[3] = int(resources.ac_temp)
        self.send_frame(frame)
        self.read_data(dataLen=8)

        frame.data[1] = mC.RTD_NET_MODE
        frame.data[3] = int(5)
        self.send_frame(frame)
        self.read_data(dataLen=8)

        frame.command = mC.MODBUS_WRITE_COIL

        frame.data[0] = 0x00
        frame.data[1] = mC.RTD_NET_ON_OFF

        if int(resources.temp_on) == 1:
            
            frame.data[2] = 0xFF
            frame.data[3] = 0x00
        else:
            frame.data[2] = 0x00
            frame.data[3] = 0x00
        
        self.send_frame(frame)
        self.read_coil_data(dataLen=6)

    def read_ac_params(self, resources):
        frame = ModbusFrame(4)
        frame.address = 0x01
        frame.command = mC.MODBUS_READ
        frame.data[0] = 0x00
        frame.data[1] = mC.RTD_NET_SETPOINT
        frame.data[2] = 0x00
        frame.data[3] = 0x01
        self.send_frame(frame)

        if self.read_data() == True:
            print(f"[INFO] Setpoint temperture: {self.frame.data[2]}")
            if self.frame.data[2] != int(resources.ac_temp):
                resources.ac_temp = self.frame.data[2]
                date_time = datetime.now()
                resources.tempdate = date_time.strftime("%Y-%m-%d %H:%M:%S")


        frame.data[1] = mC.RTD_NET_MODE
        self.send_frame(frame)

        if self.read_data() == True:
            print(f"[INFO] AC mode: {self.frame.data[2]}")

        frame.data[1] = mC.RTD_NET_FAN_SPEED
        self.send_frame(frame)

        if self.read_data() == True:
            print(f"[INFO] AC fan speed lvl: {self.frame.data[2]}")

        frame.command = mC.MODBUS_READ_COIL
        frame.data[0] = 0x00
        frame.data[1] = mC.RTD_NET_ON_OFF
        frame.data[2] = 0x00
        frame.data[3] = 0x01
        
        self.send_frame(frame)

        if self.read_coil_data(dataLen=6) == True:
            print(f"[INFO] AC state on/off: {self.frame.data[2]}")
            if self.frame.data[2] != int(resources.temp_on):
                resources.temp_on = bool(self.frame.data[2])
                date_time = datetime.now()
                resources.tempdate = date_time.strftime("%Y-%m-%d %H:%M:%S")

    
    def FlushBuffer(self):
        self.ser.flush()

    

if __name__ == "__main__":
    pass


