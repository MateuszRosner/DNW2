import sys
import random

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

        self.chart =  QChart()

        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("hh:mm:ss")
        self.axis_x.setTitleText("Date")
        self.axis_x.setMin(QtCore.QDateTime.currentDateTime())

        self.axis_y = QValueAxis()
        self.axis_y.setMax(50)

        self.dataSeries = QLineSeries()
        self.dataSeries1 = QLineSeries()

        self.chart.addSeries(self.dataSeries)
        self.chart.addSeries(self.dataSeries1)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setTitle("Energia")
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        
        self.chart.addAxis(self.axis_y, QtCore.Qt.AlignLeft)
        self.chart.addAxis(self.axis_x, QtCore.Qt.AlignBottom)

        self.dataSeries.attachAxis(self.axis_y)
        self.dataSeries.attachAxis(self.axis_x)
        self.dataSeries.setName("Seria 1")

        self.dataSeries1.attachAxis(self.axis_y)
        self.dataSeries1.attachAxis(self.axis_x)
        self.dataSeries1.setName("Seria 2")

        self.widget_2.setChart(self.chart)

        self.graph_timer = QtCore.QTimer()
        self.graph_timer.timeout.connect(self.updateChart)
        self.graph_timer.start(1000)


    def updateChart(self):
        timenow = QtCore.QDateTime.currentDateTime()

        if self.dataSeries.count() == 0:
            self.axis_x.setMin(timenow)

        self.dataSeries.append(timenow.toMSecsSinceEpoch(), random.randint(0, 50))
        self.dataSeries1.append(timenow.toMSecsSinceEpoch(), random.randint(0, 20))

        self.axis_x.setMax(timenow)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = MyWindow()
    ui.MainWindow.show()
    app.exec_()