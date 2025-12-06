import sys
from PyQt5 import QtWidgets

from Controller.Controller_main import MainWindow

def cargar_estilos(app):
    with open("Vista/EstilosVista.qss", "r") as f:
        qss = f.read()
        app.setStyleSheet(qss)
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    cargar_estilos(app)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec_())



