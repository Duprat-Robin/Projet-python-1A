from PyQt5 import QtWidgets, QtCore
import sys
import draw, airport_inspector


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    scene = draw.DrawAirport()
    inspector = airport_inspector.AirportInspector()
    inspector_dock = QtWidgets.QDockWidget()
    inspector_dock.setWidget(inspector)

    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Airport creation")
    window.setCentralWidget(scene)
    window.addDockWidget(QtCore.Qt.DockWidgetArea(1), inspector_dock)
    window.showMaximized()

    sys.exit(app.exec_())
