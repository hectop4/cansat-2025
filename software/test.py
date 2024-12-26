#Required Libraries

# Import the required libraries
import sys
from PyQt5.QtWidgets import QApplication,QMainWindow,QDesktopWidget,QVBoxLayout
from PyQt5.uic import loadUi
from PyQt5.QtCore import QIODevice,QPoint,Qt,QTimer
from PyQt5.QtSerialPort import QSerialPort,QSerialPortInfo
from PyQt5 import QtCore,QtWidgets
import pyqtgraph as pg
import numpy as np
from numpy import sin, cos, arccos, pi, round
import math
import pandas as pd
import csv
import time


# Variables
# chart Colors
GRAPH_1 = "#76C7FF"
GRAPH_2 = "#B773FF"
GRAPH_3 = "#26C999"
GRAPH_4 = "#FF6500"

#Functions:


#Main Class
class App(QMainWindow):
    """Main application."""
    def __init__(self):
        super(App,self).__init__()
        # Configura la ventana
        loadUi("hmi.ui",self)
        self.setWindowTitle("HMI")
        # Eliminar barra de título y opacidad
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(1)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
#*Iniciamos el grip para redimensionar la ventana
        self.gripsize = 10
        self.grip= QtWidgets.QSizeGrip(self)
        self.grip.resize(self.gripsize,self.gripsize)

        self.serial = QSerialPort()
        self.bt_refresh.clicked.connect(self.read_ports)
        self.bt_connect.clicked.connect(self.connect_serial)
        self.baudrate = 115200

        self.serial.readyRead.connect(self.read_serial)
    #Conectamos Puerto Serial
        self.serial = QSerialPort()
        self.bt_refresh.clicked.connect(self.read_ports)
        self.bt_connect.clicked.connect(self.connect_serial)
        self.baudrate = 115200

        self.serial.readyRead.connect(self.read_serial)


    #Charts Start
    #Configuramos las variables para los gráficos
        self.x=list(np.linspace(0,100,100))
        self.y=list(np.random.rand(100))
        self.axy=list(np.linspace(0,0,100))
        self.ayy=list(np.linspace(0,0,100))
        self.azy=list(np.linspace(0,0,100))
        self.gxy=list(np.linspace(0,0,100))
        self.gyy=list(np.linspace(0,0,100))
        self.gzy=list(np.linspace(0,0,100))
        self.t=list(np.linspace(0,0,100))
        self.p=list(np.linspace(0,0,100))
        self.h=list(np.linspace(0,0,100))
#Configuramos los colores principales de las graficas
        pg.setConfigOption('background', "#1E3E62")
        pg.setConfigOption('foreground', "white")
#% Plot_Giroscope
        self.plt_giroscope=pg.PlotWidget(title="Giroscope")
        self.gyroscope.addWidget(self.plt_giroscope)
        self.plt_giroscope.setYRange(-12,12)
        self.plt_giroscope.setXRange(0,100)
        self.plt_giroscope.showGrid(x=False,y=True)
        self.plt_giroscope.setLabel('left', "Angle", units='°')
        self.plt_giroscope.setLabel('bottom', "Time", units='s')
        self.plt_giroscope.addLegend()
        self.plt_giroscope.setMouseEnabled(x=False,y=True)
        # self.plt_giroscope.plot(self.x,self.y,pen=pg.mkPen(color=GRAPH_1,width=2),name="Angle X")
        # self.plt_giroscope.plot(self.y,self.x,pen=pg.mkPen(color=GRAPH_2,width=2),name="Angle Y")
        # self.plt_giroscope.plot(self.x,self.y,pen=pg.mkPen(color=GRAPH_3,width=2),name="Angle Z")
#%Plot_Accelerometer
        self.plt_accelerometer=pg.PlotWidget(title="Accelerometer")
        self.acceleration.addWidget(self.plt_accelerometer)
        self.plt_accelerometer.setYRange(-15,15)
        self.plt_accelerometer.setXRange(0,100)
        self.plt_accelerometer.showGrid(x=False,y=True)
        self.plt_accelerometer.setMouseEnabled(x=False,y=True)
        self.plt_accelerometer.setLabel('left', "Acceleration", units='m/s^2')
        self.plt_accelerometer.setLabel('bottom', "Time", units='s')
        self.plt_accelerometer.addLegend()

#%Plot height
        self.plt_height=pg.PlotWidget(title="Height")
        self.height.addWidget(self.plt_height)
        self.plt_height.setYRange(-20,2500)
        self.plt_height.setXRange(0,100)
        self.plt_height.showGrid(x=False,y=True)
        self.plt_height.setMouseEnabled(x=False,y=True)
        self.plt_height.setLabel('left', "Height", units='m')
        self.plt_height.setLabel('bottom', "Time", units='s')
        self.plt_height.addLegend()
#%plot pressure
        self.plt_pression=pg.PlotWidget(title="Pression")
        self.pressure.addWidget(self.plt_pression)
        self.plt_pression.setYRange(0,78000)
        self.plt_pression.setXRange(0,100)
        self.plt_pression.showGrid(x=False,y=True)
        self.plt_pression.setMouseEnabled(x=False,y=True)
        self.plt_pression.setLabel('left', "Pression", units='Pa')
        self.plt_pression.setLabel('bottom', "Time", units='s')
        self.plt_pression.addLegend()
        #self.plt_pression.plot(self.x,self.y,pen=pg.mkPen(color=GRAPH_2,width=2),name="Pression")
#%plot temperature
        self.plt_temperature=pg.PlotWidget(title="Temperature")
        self.temp.addWidget(self.plt_temperature)
        self.plt_temperature.setYRange(200,350)
        self.plt_temperature.setXRange(0,100)
        self.plt_temperature.showGrid(x=False,y=True)
        self.plt_temperature.setLabel('left', "Temperature", units='K')
        self.plt_temperature.setLabel('bottom', "Time", units='s')
        self.plt_temperature.setMouseEnabled(x=False,y=True)
        self.plt_temperature.addLegend()
        #self.plt_temperature.plot(self.x,self.y2,pen=pg.mkPen(color=GRAPH_3,width=2),name="Temperature")

#%plot speed
        self.plt_speed=pg.PlotWidget(title="Speed")
        self.speed.addWidget(self.plt_speed)
        self.plt_speed.setYRange(-180,100)
        self.plt_speed.setXRange(0,100)
        self.plt_speed.showGrid(x=False,y=True)
        self.plt_speed.setMouseEnabled(x=False,y=True)
        self.plt_speed.setLabel('left', "Speed", units='m/s')
        self.plt_speed.setLabel('bottom', "Time", units='s')
        self.plt_speed.addLegend()
        #self.plt_speed.plot(self.x,self.y1,pen=pg.mkPen(color=GRAPH_4,width=2),name="Speed")

#%Plot PPM
        self.plt_ppm=pg.PlotWidget(title="PPM")
        self.ppm.addWidget(self.plt_ppm)
        self.plt_ppm.setYRange(0,100)
        self.plt_ppm.setXRange(0,100)
        self.plt_ppm.showGrid(x=False,y=True)
        self.plt_ppm.setMouseEnabled(x=False,y=True)
        self.plt_ppm.setLabel('left', "PPM", units='ppm')
        self.plt_ppm.setLabel('bottom', "Time", units='s')
        self.plt_ppm.addLegend()
        self.plt_ppm.plot(self.x,self.y,pen=pg.mkPen(color=GRAPH_1,width=2),name="PPM")
        


        
    def read_ports(self):
        portlist=[]
        ports=QSerialPortInfo.availablePorts()
        for port in ports:
            portlist.append(port.portName())
        self.port_box.clear()
        self.port_box.addItems(portlist)

#*Conectamos el puerto serial
    def connect_serial(self):
        self.serial.waitForReadyRead(10)
        self.port=self.port_box.currentText()
        self.baud=self.baudrate
        self.serial.setBaudRate(self.baud)
        self.serial.setPortName(self.port)
        self.serial.open(QIODevice.ReadWrite)
        print('reading')
    def read_serial(self):
        if not self.serial.canReadLine(): return
        rx=self.serial.readLine()
        x=str(rx,"utf-8")
        data_dict =x
        print(data_dict)

    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_Escape and event.modifiers() == Qt.ControlModifier)or (event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier):
            self.close()





    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())