import sys
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtWidgets import  QMainWindow

from Controller.Controller_main import MainWindow

def cargar_estilos(app):
    with open("EstilosVista.qss", "r") as f:
        qss = f.read()
        app.setStyleSheet(qss)
        
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("Vista.ui", self)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    cargar_estilos(app)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec_())
