import configparser
import threading
import time

import RPi._GPIO as GPIO
import serial

from dataFrame import RedbusFrame
import redbusCommands as mC
from infrastructure import Infrastructure

TXDEN_1 = 27
TXDEN_2 = 22

BAUD_38400 = 38400
    
class Redbus():
    def __init__(self, resources, Baudrate = 38400, dev = "/dev/ttyS0", crcControl=True, dataLen=8, intervals=0.1):
        self.ser=serial.Serial(
            baudrate=Baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0.5)
        self.dev = dev
        self.ser.port = self.dev

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TXDEN_1, GPIO.OUT)
        GPIO.output(TXDEN_1, GPIO.HIGH)

        try:
            self.ser.open() 
        except serial.SerialException:
            print(f"[ERROR] Can't open serial port {self.dev}")

        self.resources = resources
        self.infrastructure = Infrastructure('/home/pi/Desktop/test/InteliHouse1.0/config.ini')
        self.frame = RedbusFrame(dataLen)
        self.rec_data_len = dataLen
        self.crc_control = crcControl
        self.transmissionInterval = intervals

        self.locker = threading.Lock()

    
    def send_frame(self, frame):
        if self.ser.isOpen():
            frame.calcCRC()
            GPIO.output(TXDEN_1, GPIO.LOW)     # transmitter
            frame = bytearray(frame)
            self.ser.write(frame)
            GPIO.output(TXDEN_1, GPIO.HIGH)    # recive

    def read_data(self):         
        if self.ser.isOpen() == True:
            data = self.ser.read(self.rec_data_len)
            data = bytearray(data)

            if len(data) < self.rec_data_len:
                self.frame.clear()
                self.ser.flush()
                # print("[WARNING] Data lenght error")
                return False
            else:
                self.frame.address = (data[0])
                self.frame.command = (data[1])
                self.frame.data.append((data[2]))
                self.frame.data.append((data[3]))
                self.frame.data.append((data[4]))
                self.frame.data.append((data[5]))
                self.frame.CRC = (data[6] & 0xFF) | (data[7] << 8)

                # check CRC
                if self.crc_control == True:
                    CRC = self.frame.CRC
                    self.frame.calcCRC()

                    if CRC != self.frame.CRC:
                        print("[WARNING] CRC error")
                        self.frame.clear()
                        self.ser.flush()
                        return False
                
                # decode data from MainBoard 
                if self.frame.address == 1:
                    try:
                        # current values of 2 ports (ports number determined by command value)                                             
                        if (self.frame.command >= mC.MAIN_BOARD_READ_CURR_1_2) and (self.frame.command <= mC.MAIN_BOARD_READ_CURR_9_10):        
                            current_val1 =   self.frame.data[1] << 8
                            current_val1 +=  self.frame.data[0]
                            
                            current_val2 =   self.frame.data[3] << 8
                            current_val2 +=  self.frame.data[2]

                            self.resources.output_currs[(self.frame.command * 2)-2] = (current_val1 / 1000.0)
                            self.resources.output_currs[(self.frame.command * 2)-1] = (current_val2 / 1000.0)

                        elif self.frame.command == mC.MAIN_BOARD_READ_DIGITAL_IN:
                            pass

                        # outputs
                        elif self.frame.command == mC.MAIN_BOARD_OUTPUTS:                                                               
                            ports =     self.frame.data[1] << 8
                            ports +=    self.frame.data[0]
                            
                            for x in range(len(self.resources.output_ports)):
                                self.resources.output_ports[x] = bool (ports & (1 << x))
                    except Exception as err:
                        print(f"[WARNING] MainBoard data format corrupted! {err}")

                # decode data from SensorsBoards
                elif self.frame.address == 15:
                    try:
                        if self.frame.command == mC.SENSORS_BOARD_READ_DISTANCE:
                            self.resources.liquids[0] = self.frame.data[0]
                            self.resources.liquids[1] = self.frame.data[1]
                            self.resources.liquids[2] = self.frame.data[2]
                            self.resources.liquids[3] = self.frame.data[3]
                    except Exception as err:
                        print(f"[WARNING] SensorsBoard data format corrupted! {err}")

                elif self.frame.address == 14:
                    try:
                        if self.frame.command == mC.SENSORS_BOARD_READ_DISTANCE:
                            self.resources.liquids[0] = self.frame.data[0]
                            self.resources.liquids[1] = self.frame.data[1]
                            self.resources.liquids[2] = self.frame.data[2]
                            self.resources.liquids[3] = self.frame.data[3]
                    except Exception as err:
                        print(f"[WARNING] SensorsBoard data format corrupted! {err}")
                
                # decode data from AmbientBoards
                elif self.frame.address == 13:
                    try:
                        if self.frame.command == mC.AMBIENT_BOARD_READ_TEMP_PRESS:
                            self.resources.temperature[2]   = (self.frame.data[1] << 8 | self.frame.data[0]) - 30
                            self.resources.pressure[2]      = self.frame.data[3] << 8 | self.frame.data[2]

                        elif self.frame.command == mC.AMBIENT_BOARD_READ_HUMID_GAS:
                            self.resources.humidity[2]      = self.frame.data[1] << 8 | self.frame.data[0]
                    except Exception as err:
                        print(f"[WARNING] AmbientBoard data format corrupted! {err}")

                elif self.frame.address == 12:
                    try:
                        if self.frame.command == mC.AMBIENT_BOARD_READ_TEMP_PRESS:
                            self.resources.temperature[1]   = (self.frame.data[1] << 8 | self.frame.data[0]) - 30
                            self.resources.pressure[1]      = self.frame.data[3] << 8 | self.frame.data[2]

                        elif self.frame.command == mC.AMBIENT_BOARD_READ_HUMID_GAS:
                            self.resources.humidity[1]      = self.frame.data[1] << 8 | self.frame.data[0]
                    except Exception as err:
                        print(f"[WARNING] AmbientBoard data format corrupted! {err}")

                elif self.frame.address == 11:
                    try:
                        if self.frame.command == mC.AMBIENT_BOARD_READ_TEMP_PRESS:
                            self.resources.temperature[0]   = (self.frame.data[1] << 8 | self.frame.data[0]) - 30
                            self.resources.pressure[0]      = self.frame.data[3] << 8 | self.frame.data[2]

                        elif self.frame.command == mC.AMBIENT_BOARD_READ_HUMID_GAS:
                            self.resources.humidity[0]      = self.frame.data[1] << 8 | self.frame.data[0]
                    except Exception as err:
                        print(f"[WARNING] AmbientBoard data format corrupted! {err}")

                self.frame.data.clear()
                return True
    
    def startUpdates(self):
        self.updateThread = threading.Thread(target=self.updateData)
        self.updateThread.daemon = True
        self.updateThread.start()
        print("[INFO] Modbus data update thread started....")

    def stopUpdates(self):
        self.locker.acquire(blocking=True, timeout=2)
        time.sleep(1)
        print("[INFO] Modbus data update thread stopped....")

    def resumeUpdates(self):
        self.locker.release()
        print("[INFO] Modbus data update thread released....")

    def setSensorsBoardMode(self, mode):
        dataFrame = RedbusFrame(4)

        self.stopUpdates()

        if self.infrastructure.infrastructure['SensorsBoards'] != '0':
            # ------------- SET MODE -----------------------
            for x, adr in enumerate(self.infrastructure.sensorsBoards):
                dataFrame.address = int(adr)
                dataFrame.command = mC.MODBUS_WRITE
                dataFrame.data[0] = mC.SENSORS_BOARD_SET_MODE
                dataFrame.data[2] = mode
                self.send_frame(dataFrame)

                time.sleep(self.transmissionInterval)

        self.resumeUpdates()

    def updateData(self):
        while self.ser.isOpen() == True:
            dataFrame = RedbusFrame(4)
            # SensorsBoard query
            if self.infrastructure.infrastructure['SensorsBoards'] != '0':
                for adr in self.infrastructure.sensorsBoards:
                    dataFrame.address = int(adr)
                    dataFrame.command = mC.MODBUS_READ
                    dataFrame.data[0] = mC.SENSORS_BOARD_READ_DISTANCE
                    self.send_frame(dataFrame)
                    if (self.read_data() == False):
                        print( f"[ERROR] Module SonsorBoard on address: {dataFrame.address} failure")

            # MainBoards queries
            if self.infrastructure.infrastructure['MainBoards'] != '0':        
                for adr in self.infrastructure.mainBoards:
                    # set outputs ragardless to checkboxes
                    dataFrame.address = int(adr)
                    dataFrame.command = mC.MODBUS_WRITE
                    dataFrame.data[0] = mC.MAIN_BOARD_OUTPUTS
                    dataFrame.data[2] = (self.resources.relays & 0xFF)
                    dataFrame.data[3] = ((self.resources.relays >> 8) & 0xFF)

                    self.send_frame(dataFrame)
                    time.sleep(self.transmissionInterval)

                    # read outputs states
                    dataFrame.address = int(adr)
                    dataFrame.command = mC.MODBUS_READ
                    dataFrame.data[0] = mC.MAIN_BOARD_OUTPUTS
                    self.send_frame(dataFrame)
                    if (self.read_data() == False):
                        print( f"[ERROR] Module MainBoard on address: {dataFrame.address} failure")
                    time.sleep(self.transmissionInterval)

                    # read channels currents
                    for x in range(1,6):
                        dataFrame.address = int(adr)
                        dataFrame.command = mC.MODBUS_READ
                        dataFrame.data[0] = x
                        self.send_frame(dataFrame)
                        if (self.read_data() == False):
                            print( f"[ERROR] Module MainBoard on address: {dataFrame.address} failure")
                        time.sleep(self.transmissionInterval)

            # AmbientBoards queries
            if self.infrastructure.infrastructure['AmbientBoards'] != '0':        
                for adr in self.infrastructure.ambientBoards:
                    # temperature and pressure
                    dataFrame.address = int(adr)
                    dataFrame.command = mC.MODBUS_READ
                    dataFrame.data[0] = mC.AMBIENT_BOARD_READ_TEMP_PRESS
                    self.send_frame(dataFrame)
                    if (self.read_data() == False):
                        print( f"[ERROR] Module AmbientBoard on address: {dataFrame.address} failure")
                    time.sleep(self.transmissionInterval)

                    # read humidity and IAQ
                    dataFrame.address = int(adr)
                    dataFrame.command = mC.MODBUS_READ
                    dataFrame.data[0] = mC.AMBIENT_BOARD_READ_HUMID_GAS
                    self.send_frame(dataFrame)
                    if (self.read_data() == False):
                        print( f"[ERROR] Module AmbientBoard on address: {dataFrame.address} failure")
                    time.sleep(self.transmissionInterval)

            while(self.locker.locked()):
                pass

    def initiate_modules(self):
        dataFrame = RedbusFrame(4)
        print("\n[INFO] Modules initialization....")
        if self.infrastructure.infrastructure['MainBoards'] != '0':
            print("[INFO] MainBoards configured...")

        if self.infrastructure.infrastructure['SensorsBoards'] != '0':
            # ------------- SET RELAY MODE -----------------------
            for x, adr in enumerate(self.infrastructure.sensorsBoards):
                dataFrame.address = int(adr)
                dataFrame.command = mC.MODBUS_WRITE
                dataFrame.data[0] = mC.SENSORS_BOARD_RELAY_MODE
                dataFrame.data[2] = int(self.infrastructure.config['SENSORS_INPUTS']['RelayMode'].split(',')[x])
                self.send_frame(dataFrame)

                time.sleep(self.transmissionInterval)

            # ------------- SET THRESHOLDS -----------------------
            for x, adr in enumerate(self.infrastructure.sensorsBoards):
                thr_min = int(self.infrastructure.config['SENSORS_INPUTS']['PercentThMin'].split(',')[x])
                thr_max = int(self.infrastructure.config['SENSORS_INPUTS']['PercentThMax'].split(',')[x])
                dataFrame.address = int(adr)
                dataFrame.command = mC.MODBUS_WRITE
                dataFrame.data[0] = mC.SENSORS_BOARD_THRESHOLDS
                dataFrame.data[2] = thr_max
                dataFrame.data[3] = thr_min
                self.send_frame(dataFrame)

                time.sleep(self.transmissionInterval)

            # ------------- SET MIN MAX RAW -----------------------
            for x, adr in enumerate(self.infrastructure.sensorsBoards):
                raw_min = int(self.infrastructure.config['SENSORS_INPUTS']['MinRaw'].split(',')[x])
                raw_max = int(self.infrastructure.config['SENSORS_INPUTS']['MaxRaw'].split(',')[x])
                dataFrame.address = int(adr)
                dataFrame.command = mC.MODBUS_WRITE
                dataFrame.data[0] = mC.SENSORS_BOARD_RAW_VALUES
                dataFrame.data[2] = raw_max
                dataFrame.data[3] = raw_min
                self.send_frame(dataFrame)

                time.sleep(self.transmissionInterval)


            print("[INFO] SensorsBoards configured...")
        
        if self.infrastructure.infrastructure['AmbientBoards'] != '0':
            print("[INFO] AmbientBoards configured...")

        if self.infrastructure.infrastructure['PGMBoards'] != '0':
            print("[INFO] PGMBoards configured...")

        print("[INFO] Initialization done!\n")   

    def FlushBuffer(self):
        self.ser.flush()

    

if __name__ == "__main__":
    f = RedbusFrame(4)

    length = len(f) -2 
    
    f.address = 1
    f.command = 3

    f.__iter__()

    while(length):
        print(f.__next__())
        length -= 1

    f.calcCRC()
    print(f.CRC)


