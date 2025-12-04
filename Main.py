import sys
from PyQt5 import QtWidgets

from Controller.Controller_main import MainWindow


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec_())
