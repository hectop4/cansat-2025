#start hmi.ui file with pyqt5

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtCore
from PyQt5 import uic

#remove the window title bar

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowFlags(QtCore.Qt.FramelessWindowHint)
uic.loadUi("hmi.ui", window)
window.show()
sys.exit(app.exec_())