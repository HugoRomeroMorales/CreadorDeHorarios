import sys
import os
from PyQt5 import QtWidgets

from Controller.Controller_main import MainWindow

def cargar_estilos(app):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_qss = os.path.join(base_dir, "Vista", "EstilosVista.qss")

    try:
        with open(ruta_qss, "r", encoding="utf-8") as f:
            qss = f.read()
            app.setStyleSheet(qss)
    except FileNotFoundError:
        print("No se encontró EstilosVista.qss en:", ruta_qss)
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    cargar_estilos(app)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec_())



