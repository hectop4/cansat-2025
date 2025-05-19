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
        self.m=list(np.linspace(0,0,100))
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
        if not self.serial.canReadLine(): 
            return  # <-- Importante salir aquí si no hay datos

        rx = self.serial.readLine()
        x = str(rx, "utf-8").strip()
        print('Raw Data:', x)  # Verifica los datos crudos que llegan
        data_dict = parse_text_to_dict(x)
        print("Parsed Data: ", data_dict)  # Revisa el formato del diccionario resultante

        try:
            if 'T' in data_dict:
                self.temperature_value = float(data_dict['T']) + 273.15

            if 'P' in data_dict:
                self.pressure_value = float(data_dict['P'])

            if 'H' in data_dict:
                self.height_value = float(data_dict['H'])

            if 'M' in data_dict:
                self.ppm_value = float(data_dict['M'])  # Cambia a un nombre temporal

            self.update_graphs()  # Actualizar solo cuando tengas nuevos datos

        except ValueError as e:
            print(f"ValueError encountered: {e}")
            pass

    #*Actualizamos los graficos
    def update_graphs(self):
        """
        Updates the graphs when Temperature, Pressure and Height values are available.
        """
        if hasattr(self, 'temperature_value') and hasattr(self, 'pressure_value') and hasattr(self, 'height_value') and hasattr(self, 'ppm_value'):
            self.x.append(self.x[-1] + 1 if self.x else 0)
            self.t.append(self.temperature_value)
            self.p.append(self.pressure_value)
            self.h.append(self.height_value)
            self.m.append(self.ppm_value)  # Agrega el valor a la lista

            max_length = 1000
            if len(self.x) > max_length:
                self.x = self.x[-max_length:]
                self.t = self.t[-max_length:]
                self.p = self.p[-max_length:]
                self.h = self.h[-max_length:]
                self.m = self.m[-max_length:]

            # Actualizar gráficas
            self.plt_temperature.clear()
            self.plt_temperature.plot(self.x, self.t, pen=pg.mkPen(color=GRAPH_3, width=2), name="Temperature")
            self.plt_temperature.enableAutoRange(axis='x', enable=True)

            self.plt_pression.clear()
            self.plt_pression.plot(self.x, self.p, pen=pg.mkPen(color=GRAPH_4, width=2), name="Pressure")
            self.plt_pression.enableAutoRange(axis='x', enable=True)

            self.plt_height.clear()
            self.plt_height.plot(self.x, self.h, pen=pg.mkPen(color=GRAPH_2, width=2), name="Height")
            self.plt_height.enableAutoRange(axis='x', enable=True)

            self.plt_ppm.clear()
            self.plt_ppm.plot(self.x, self.m, pen=pg.mkPen(color=GRAPH_1, width=2), name="PPM")
            self.plt_ppm.enableAutoRange(axis='x', enable=True)





    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_Escape and event.modifiers() == Qt.ControlModifier)or (event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier):
            self.close()





def parse_text_to_dict(text):
    """
    Parses a text string and extracts the values of T, P, M, and H.
    """
    result = {}

    # Dividimos el texto en elementos separados por comas
    items = text.split(",")
    print(f"Items: {items}")  # Verificar cómo se dividen los datos

    for item in items:
        # Buscamos las claves T, P, M, H y extraemos el valor correspondiente
        if item.startswith("T"):  # Temperatura
            key = "T"
            value = item[2:]  # El valor sigue a la "T", así que eliminamos la "T"
            result[key] = value.strip()
            print(f"Parsed {key}: {value.strip()}")  # Verificar qué estamos extrayendo
        
        elif item.startswith("P"):  # Presión
            key = "P"
            value = item[2:]  # Extraemos el valor después de "P"
            result[key] = value.strip()
            print(f"Parsed {key}: {value.strip()}")  # Verificar qué estamos extrayendo
        
        elif item.startswith("M"):  # PPM
            key = "M"
            value = item[2:]  # Extraemos el valor después de "M"
            result[key] = value.strip()
            print(f"Parsed {key}: {value.strip()}")  # Verificar qué estamos extrayendo
        
        elif item.startswith("H"):  # Altura
            key = "H"
            value = item[2:]  # Extraemos el valor después de "H"
            result[key] = value.strip()
            print(f"Parsed {key}: {value.strip()}")  # Verificar qué estamos extrayendo

    return result

    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())