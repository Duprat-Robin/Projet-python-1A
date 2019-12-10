from PyQt5 import QtWidgets
import sys
import draw, file_airport


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    scene = draw.DrawAirport()

    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Airport creation")
    window.setCentralWidget(scene)
    window.showMaximized()

    sys.exit(app.exec_())
