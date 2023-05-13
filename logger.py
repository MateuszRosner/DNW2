import sys
import os

from datetime import datetime

LABELS = {"Date" : " ", "Time" : " ", "PowTotal" : "0.0", "WodaPitna1" : "0", "WodaPitna2" : "0", "WodaBrudna" : "0",  "Szambo" : "0", "Paliwo" : "0", 
          "TempSalon" : "0.0", "TempKuchnia" : "0.0", "TempTaras" : "0.0", "PressSalon" : "0.0", "PressTaras" : "0.0",
          "HumidSalon" : "0.0", "HumidKuchnia" : "0.0", "HumidTaras" : "0.0"}

class Logger():
    def __init__(self):
        path = os.getcwd()
        path = os.path.join(path, "logs")

        # check if path exists
        if not os.path.exists(path=path):
            try:
                os.makedirs(path)
                print("[INFO] Logger directory created")
            except Exception as msg:
                print(f"Error {msg} occured....")

        else:
            print("[INFO] Logger directory already exists")

    def logData(self, resources):
        date = datetime.now().strftime("%Y_%m_%d")
        time = datetime.now().strftime("%H:%M:%S")

        # check if log file exists 
        path = os.getcwd()
        path = os.path.join(path, "logs")

        if not os.path.exists(path=path):
            try:
                os.makedirs(path)
            except Exception as msg:
                print(f"Error {msg} occured....")
           
        if not os.path.exists(os.path.join(path, date)):
            with open(os.path.join(path, date), 'w') as f:
                f.write(",".join(list(LABELS.keys())) + '\n')

        _labels = LABELS

        _labels["Date"] = date
        _labels["Time"] = time
        _labels["PowTotal"] = str(resources.total_curr)
        _labels["WodaPitna1"] = str(resources.liquids[0])
        _labels["WodaPitna2"] = str(resources.liquids[1])
        _labels["WodaBrudna"] = str(resources.liquids[2])
        _labels["Szambo"] = str(resources.liquids[3])
        _labels["Paliwo"] = str(resources.liquids[4])
        _labels["TempSalon"] = str(resources.temperature[0]/10)
        _labels["TempKuchnia"] = str(resources.temperature[1]/10)
        _labels["TempTaras"] = str(resources.temperature[2]/10)
        _labels["PressSalon"] = str(resources.pressure[0]/10)
        _labels["PressKuchnia"] = str(resources.pressure[1]/10)
        _labels["PressTaras"] = str(resources.pressure[2]/10)
        _labels["HumidSalon"] = str(resources.humidity[0]/10)
        _labels["HumidKuchnia"] = str(resources.humidity[1]/10)
        _labels["HumidTaras"] = str(resources.humidity[2]/10)

        with open(os.path.join(path, date), 'a') as f:
            f.write(",".join(list(LABELS.values())) + '\n')
