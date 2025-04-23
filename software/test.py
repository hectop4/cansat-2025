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

    
        def create_plot(widget, title, y_range, x_range, y_label, y_units, x_label, x_units, color=None, name=None):
            plot = pg.PlotWidget(title=title)
            widget.addWidget(plot)
            plot.setYRange(*y_range)
            plot.setXRange(*x_range)
            plot.showGrid(x=False, y=True)
            plot.setMouseEnabled(x=False, y=True)
            plot.setLabel('left', y_label, units=y_units)
            plot.setLabel('bottom', x_label, units=x_units)
            plot.addLegend()
            # if color and name:
                # plot.plot(self.x, self.y, pen=pg.mkPen(color=color, width=2), name=name)
            return plot

        # Create and configure all plots
        self.plt_giroscope = create_plot(self.gyroscope, "Giroscope", (-12, 12), (0, 100), "Angle", "°", "Time", "s")
        self.plt_accelerometer = create_plot(self.acceleration, "Accelerometer", (-15, 15), (0, 100), "Acceleration", "m/s^2", "Time", "s")
        self.plt_height = create_plot(self.height, "Height", (-20, 2500), (0, 100), "Height", "m", "Time", "s")
        self.plt_pression = create_plot(self.pressure, "Pression", (0, 78000), (0, 100), "Pression", "Pa", "Time", "s")
        self.plt_temperature = create_plot(self.temp, "Temperature", (260, 300), (0, 100), "Temperature", "K", "Time", "s")
        self.plt_speed = create_plot(self.speed, "Speed", (-180, 100), (0, 100), "Speed", "m/s", "Time", "s")
        self.plt_ppm = create_plot(self.ppm, "PPM", (0, 100), (0, 100), "PPM", "ppm", "Time", "s", GRAPH_1, "PPM")

    # Create and configure the main layout        


        
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
        print("Data: ",parse_text_to_dict(data_dict))
        data_dict=parse_text_to_dict(data_dict)
        try:
            # Recortar self.x para mantener el mismo tamaño que las demás listas
            self.x = self.x[1:]

            # Gráfico de temperatura
            self.t = self.t[1:]
            self.t.append(float(data_dict['T']) + 273.15)
            self.plt_temperature.clear()
            self.plt_temperature.plot(self.x, self.t, pen=pg.mkPen(color=GRAPH_3, width=2), name="Temperature")

            # Gráfico de presión
            self.p = self.p[1:]
            self.p.append(float(data_dict['P']))
            self.plt_pression.clear()
            self.plt_pression.plot(self.x, self.p, pen=pg.mkPen(color=GRAPH_4, width=2), name="Pressure")

            # Gráfico de altura
            self.h = self.h[1:]
            self.h.append(float(data_dict['H']))
            self.plt_height.clear()
            self.plt_height.plot(self.x, self.h, pen=pg.mkPen(color=GRAPH_2, width=2), name="Height")

            # Gráfico de PPM
            self.ppm = self.ppm[1:]
            self.ppm.append(float(data_dict['PPM']))
            self.plt_ppm.clear()
            self.plt_ppm.plot(self.x, self.ppm, pen=pg.mkPen(color=GRAPH_1, width=2), name="PPM")

        except ValueError as e:
            # Log the error and skip the corrupt value
            print(f"ValueError encountered: {e}")
            pass
            

    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_Escape and event.modifiers() == Qt.ControlModifier)or (event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier):
            self.close()


def parse_text_to_dict(text):
  """
  Parses a text string into a dictionary. Each item is separated by commas,
  and key-value pairs are separated by colons. The first two items are discarded.
  """
  items = text.split(",")[2:]  # Discard the first two items
  result = {}
  for item in items:
    if ":" in item:
      key, value = item.split(":", 1)
      result[key.strip()] = value.strip()
  return result


    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())