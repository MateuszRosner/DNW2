import sys
import time
import datetime

import redbus
import configparser
import redbusCommands as mC
import modbus
import remoteClient

from logger    import Logger
from resources import Resources

from InteliHouseUI import Ui_MainWindow
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PyQt5.QtCore import Qt


class MyWindow(Ui_MainWindow):
# ---------------class init functions---------------
    def __init__(self):
        super(MyWindow, self).__init__()
        self.MainWindow = QtWidgets.QMainWindow()
        self.setupUi(self.MainWindow)

        # init objects
        self.resources = Resources()
        self.redbus = redbus.Redbus(resources=self.resources, dev="/dev/ttySC0")
        self.modbus = modbus.Modbus(dev="/dev/ttySC1", dataLen=7)
        # self.modbus = modbus.Modbus(self.resources, dev="/dev/ttySC1", dataLen=6, crcControl=False)

        self.frame = redbus.RedbusFrame(4)

        self.timer = QtCore.QTimer()
        self.graph_timer = QtCore.QTimer()

        self.chartPower     =  QChart()
        self.chartResources =  QChart()
        self.axis_y_p = QValueAxis()
        self.axis_y_r = QValueAxis()
        self.axis_x_p = QDateTimeAxis()
        self.axis_x_r = QDateTimeAxis()

        self.axis_x_p.setFormat("hh:mm:ss")
        self.axis_x_p.setTitleText("Czas")
        self.axis_x_r.setFormat("hh:mm:ss")
        self.axis_x_r.setTitleText("Czas")

        self.axis_y_p.setTitleText("kW")

        # create graphs data series
        self.powerData = QLineSeries(self.MainWindow)
        self.powerData.setName("Total")

        self.tempsData = [QLineSeries(self.MainWindow), QLineSeries(self.MainWindow), QLineSeries(self.MainWindow)]
        self.tempsData[0].setName("Salon")
        self.tempsData[1].setName("Kuchnia")
        self.tempsData[2].setName("Taras")

        self.pressData = [QLineSeries(self.MainWindow), QLineSeries(self.MainWindow), QLineSeries(self.MainWindow)]
        self.pressData[0].setName("Salon")
        self.pressData[1].setName("Kuchnia")
        self.pressData[2].setName("Taras")

        self.humidData = [QLineSeries(self.MainWindow), QLineSeries(self.MainWindow), QLineSeries(self.MainWindow)]
        self.humidData[0].setName("Salon")
        self.humidData[1].setName("Kuchnia")
        self.humidData[2].setName("Taras")

        self.liquidData = [QLineSeries(self.MainWindow), QLineSeries(self.MainWindow), QLineSeries(self.MainWindow), QLineSeries(self.MainWindow), QLineSeries(self.MainWindow)]
        self.liquidData[0].setName("Woda pitna 1")
        self.liquidData[1].setName("Woda brudna")
        self.liquidData[2].setName("Szambo")
        self.liquidData[3].setName("Paliwo")
        self.liquidData[4].setName("Woda pitna 2")

        self.setGraphs()

        # GUI elements init - labels, progressbars
        self.progressBars = [self.progressBar1, self.progressBar2, self.progressBar3, self.progressBar4, 
                             self.progressBar5, self.progressBar6, self.progressBar7, self.progressBar8, 
                             self.progressBar9, self.progressBar10, self.progressBarWP, self.progressBarWB,
                             self.progressBarSZ, self.progressBarFU, self.progressBarFU_2,self.progressBarTotalCurr]
        self.pwrLabels = [self.labelPwr1_1, self.labelPwr1_2,  self.labelPwr1_3, self.labelPwr1_4, self.labelPwr1_5,
                           self.labelPwr1_6,  self.labelPwr1_7, self.labelPwr1_8, self.labelPwr1_9, self.labelPwr1_10,]

        self.checkBoxes = [self.checkBox1, self.checkBox2, self.checkBox3, self.checkBox4, self.checkBox5,
                           self.checkBox6, self.checkBox7, self.checkBox8, self.checkBox9, self.checkBox10]

        self.temperatures = [self.label_temp0, self.label_temp1, self.label_temp2]
        self.pressures    = [self.label_press0, self.label_press1, self.label_press2]
        self.humidities   = [self.label_hum0, self.label_hum1, self.label_hum2]
        self.iaqs         = []

        # misc variables
        self.logger = Logger()
        self.prescaller = 1
        self.counter = 0

        # --------------- config file reading    ---------------
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self.refreshTime            = int(self.config['PARAMETERS']['RefreshFrequency'])
        self.mainOutputs            = self.config['MAIN_OUTPUTS']
        self.maxSamples             = int(self.config['CHARTS']['MaxSamples'])
        self.priorities             = self.config['MAIN_OUTPUTS']['Priorities'].split(',')

        self.infrastructure         = self.config['INFRASTRUCTURE']
        self.addresses              = self.config['ADDRESSES']
        
        # run REDBUS and initiate modules
        self.redbus.initiate_modules()
        self.redbus.startUpdates()

        # --------------- signals - slots config ---------------
        self.timer.timeout.connect(self.refresh_ui)
        self.graph_timer.timeout.connect(self.create_linechart)
        self.ButtonClearGraphs.clicked.connect(self.clearGraphs)
        self.ButtonTank.clicked.connect(self.setTankMode)

        self.timer.start(self.refreshTime)
        self.graph_timer.start(self.refreshTime)

# ---------------class usage functions---------------
    """
    cyclic gui refresh with updated parameters from modules
    """
    def refresh_ui(self): 
        self.resources.relays = 0   
        for x, box in enumerate(self.checkBoxes):
            self.resources.relays += (int(box.isChecked())) << x

        self.refresh_progressBars()

        self.prescaller -= 1
        if self.prescaller == 0:
            self.logger.logData(self.resources)
            self.prescaller = int(self.config['LOGGER']['Prescaller'])
            token = remoteClient.log_to_panel()
            response = remoteClient.send_test_data(token, self.resources)

            try:
                for idx in range(1, 11, 1):
                    self.resources.relays[idx-1] = int(bool(response[f"output{idx}"]))    
            except Exception as err:
                print(f'Other error occurred: {err}')

            self.refresh_checkBoxes()

        self.modbus.Test()

    """
    refresh progres bars 
    """
    def refresh_progressBars(self):
        avg_calbration = 0.0
        channels = 0
        for val in self.mainOutputs['Calibration'].split(','):
            avg_calbration += int(val)
            channels += 1
        
        avg_calbration = avg_calbration / channels

        # refresh currents progress bars
        for x, val in enumerate(self.resources.output_currs):
            self.progressBars[x].setValue(val * 50 // (int(self.mainOutputs['Calibration'].split(',')[x])))

        # refresh channel pwr labels
        for x,label in enumerate(self.pwrLabels):
            label.setText("{:.2f} kW" .format((self.resources.output_currs[x] / avg_calbration)))

        # refresh liquids progress bars
        for x, val in enumerate(self.resources.liquids):
            self.progressBars[10 + x].setValue(val)

        # refresh total current progress bar
        self.progressBarTotalCurr.setValue(sum(self.resources.output_currs) / avg_calbration * 10)
        self.label_11.setText("{:.2f} kWh" .format(sum(self.resources.output_currs) / avg_calbration))

        for x, temp in enumerate(self.temperatures):
            temp.setText(f"{self.resources.temperature[x] / 10} *C")
        
        for x, press in enumerate(self.pressures):
            press.setText(f"{self.resources.pressure[x] / 10} hPa")
        
        for x, hum in enumerate(self.humidities):
            hum.setText(f"{self.resources.humidity[x] / 10} %")
        

    def refresh_checkBoxes(self):
        for x, val in enumerate(self.resources.output_ports):
            self.checkBoxes[x].setChecked(bool(val))

    def clearGraphs(self):
        self.counter = 0

        # clear resources data banks
        self.powerData.clear()

        for temp in self.tempsData:
            temp.clear()
        for press in self.pressData:
            press.clear()
        for humi in self.humidData:
            humi.clear()
        for liquid in self.liquidData:
            liquid.clear()

    def setGraphs(self):
        self.chartPower.addSeries(self.powerData)
        self.chartPower.setAnimationOptions(QChart.NoAnimation)
        self.chartPower.setTitle("Energia")
        self.chartPower.legend().setVisible(True)
        self.chartPower.legend().setAlignment(Qt.AlignBottom)
        self.chartPower.addAxis(self.axis_y_p, QtCore.Qt.AlignLeft)
        self.chartPower.addAxis(self.axis_x_p, QtCore.Qt.AlignBottom)

        self.powerData.attachAxis(self.axis_x_p)
        self.powerData.attachAxis(self.axis_y_p)

        self.widget_2.setChart(self.chartPower)

        self.chartResources.setAnimationOptions(QChart.NoAnimation)
        self.chartResources.legend().setVisible(True)
        self.chartResources.legend().setAlignment(Qt.AlignBottom)
        self.chartResources.addAxis(self.axis_y_r, QtCore.Qt.AlignLeft)
        self.chartResources.addAxis(self.axis_x_r, QtCore.Qt.AlignBottom)

        for series in self.tempsData:
            self.chartResources.addSeries(series)
            series.attachAxis(self.axis_x_r)
            series.attachAxis(self.axis_y_r)
            series.setVisible(False) 
         
        for series in self.pressData:
            self.chartResources.addSeries(series)
            series.attachAxis(self.axis_x_r)
            series.attachAxis(self.axis_y_r)
            series.setVisible(False)
            
        for series in self.humidData:
            self.chartResources.addSeries(series)
            series.attachAxis(self.axis_x_r)
            series.attachAxis(self.axis_y_r)
            series.setVisible(False)

        for series in self.liquidData:
            self.chartResources.addSeries(series)
            series.attachAxis(self.axis_x_r)
            series.attachAxis(self.axis_y_r)
            series.setVisible(False)
        
        self.widget.setChart(self.chartResources)

    def create_linechart(self):
        timenow = QtCore.QDateTime.currentDateTime()

        if self.powerData.count() == 0:
            self.axis_x_p.setMin(timenow)

        if self.tempsData[0].count() == 0:
            self.axis_x_r.setMin(timenow)

        self.powerData.append(timenow.toMSecsSinceEpoch(), self.progressBarTotalCurr.value()/10)
        self.axis_x_p.setMax(timenow)
        self.axis_x_r.setMax(timenow)

        self.axis_y_p.setMax(10)

        for idx, series in enumerate(self.tempsData):
                series.setVisible(self.radioButtonTemp.isChecked())
                series.append(timenow.toMSecsSinceEpoch(), self.resources.temperature[idx] / 10)
        
        for idx, series in enumerate(self.pressData):
                series.setVisible(self.radioButtonPress.isChecked())
                series.append(timenow.toMSecsSinceEpoch(), self.resources.pressure[idx] / 10)

        for idx, series in enumerate(self.humidData):
                series.setVisible(self.radioButtonHumid.isChecked())
                series.append(timenow.toMSecsSinceEpoch(), self.resources.humidity[idx] / 10)

        for idx, series in enumerate(self.liquidData):
                series.setVisible(self.radioButtonLiquids.isChecked())
                series.append(timenow.toMSecsSinceEpoch(), self.resources.liquids[idx] / 10)

        if self.radioButtonTemp.isChecked() == True:
            self.chartResources.setTitle("Temperatura")
            self.axis_y_r.setMax(50)
            
        elif self.radioButtonPress.isChecked() == True:
            self.chartResources.setTitle("Cisnienie")
            self.axis_y_r.setMax(1200)
            
        elif self.radioButtonHumid.isChecked() == True:
            self.chartResources.setTitle("Wilgotność")
            self.axis_y_r.setMax(100)
 
        elif self.radioButtonLiquids.isChecked() == True:
            self.chartResources.setTitle("Płyny")
            self.axis_y_r.setMax(100)

        self.counter = self.counter + 1

        if self.counter >= self.maxSamples:
            self.clearGraphs()

    def setTankMode(self):
        if self.ButtonTank.isChecked() == False:
            self.redbus.setSensorsBoardMode(mC.SENSORS_BOARD_MODE_TANKING)
            self.ButtonTank.setChecked(True)
        else:
            self.redbus.setSensorsBoardMode(mC.SENSORS_BOARD_MODE_NORMAL)
            self.ButtonTank.setChecked(False)

        
    def __del__(self):
        pass



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = MyWindow()
    ui.MainWindow.show()
    app.exec_()
    ui.__del__()    # clear all relays outputs in MainBoard
    print("Finish")