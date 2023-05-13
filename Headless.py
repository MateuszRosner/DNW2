import sys
import time
import datetime
import threading

import redbus
import configparser
import redbusCommands as mC
import modbus
import remoteClient

from logger    import Logger
from resources import Resources

from PyQt5 import QtCore, QtWidgets

class App():
    def __init__(self):
        # --------------- config file reading    ---------------
        self.config = configparser.ConfigParser()
        
        # try to read config file
        while True:
            try:
                self.config.read('./config.ini')

                self.refreshTime            = int(self.config['PARAMETERS']['RefreshFrequency'])
                self.mainOutputs            = self.config['MAIN_OUTPUTS']
                self.maxSamples             = int(self.config['CHARTS']['MaxSamples'])
                self.priorities             = self.config['MAIN_OUTPUTS']['Priorities'].split(',')

                self.infrastructure         = self.config['INFRASTRUCTURE']
                self.addresses              = self.config['ADDRESSES']
            except Exception as err:
                print(f"[INFO] Config file issu {err}")
                time.sleep(1)
            else:
                print(f"[INFO] Config file loaded")
                break
        
        # init objects
        self.resources = Resources()
        self.redbus = redbus.Redbus(resources=self.resources, dev="/dev/ttySC0")
        self.modbus = modbus.Modbus(dev="/dev/ttySC1", dataLen=7, crcControl=False)

        self.frame = redbus.RedbusFrame(4)

        # misc variables
        #self.logger = Logger()
        self.prescaller = 1
        self.counter = 0
        
        # run REDBUS and initiate modules
        self.redbus.initiate_modules()
        self.redbus.startUpdates()

        print("[INFO] Application initialized properly")

    def refresh(self): 
        self.modbus.read_ac_params(self.resources)
        print(self.resources.temperature)
        print(self.resources.output_currs)

        self.prescaller -= 1
        if self.prescaller == 0:
            #self.logger.logData(self.resources)
            self.prescaller = int(self.config['LOGGER']['Prescaller'])
            
            token = remoteClient.log_to_panel()
            response = remoteClient.send_test_data(token, self.resources)
            test_relays = 0
            try:
                for idx in range(1, 11, 1):
                    test_relays |= (int(bool(response[f"output{idx}"])) << (idx-1))  
                
                self.resources.relays = test_relays
                self.resources.ac_temp = response["temp_set"]
                self.resources.temp_on = bool(response["temp_on"])
                self.resources.anti_freez = bool(response["freeze_protect"])
                self.modbus.set_ac_params(self.resources)
            except Exception as err:
                print(f'Other error occurred: {err}')                


if __name__ == "__main__":
    app = App()
    time.sleep(5)
    
    while threading.main_thread().is_alive():
        try:
            #app.redbus.updateData()
            app.refresh()
        except Exception as err:
            print(f"Exception {err} occured")
        finally:
            time.sleep(1)
            if not app.redbus.updateThread.is_alive():
                app.redbus.startUpdates()
    
    print("Finish")