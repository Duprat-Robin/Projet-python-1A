"""Main module for the Python Airport code"""

from PyQt5 import QtWidgets, QtCore

import airport
import inspector
import radarview
import simulation
import traffic

APT_FILE = ("DATA/lfpg_map.txt", "DATA/lfpo_map.txt")
PLN_FILE = ("DATA/lfpg_flights.txt", "DATA/lfpo_flights.txt")

if __name__ == "__main__":
    # Load files
    # choice = 0 if input("1: Roissy / [2: Orly] ? ") == '1' else 1
    choice = 0
    apt = airport.from_file(APT_FILE[choice])
    flights = traffic.from_file(apt, PLN_FILE[choice])

    # create the simulation
    sim = simulation.Simulation(apt, flights)

    # Initialize Qt
    app = QtWidgets.QApplication([])

    # create the radar view and the time navigation interface
    rad = radarview.RadarView(sim)
    rad.move(10, 10)

    # create the inspector
    insp = inspector.Inspector(rad)

    # create a QDockWidget for the inspector
    insp_dock = QtWidgets.QDockWidget()
    insp_dock.setWidget(insp)

    # create the QMainWindow and add both widgets
    win = QtWidgets.QMainWindow()
    win.setWindowTitle("AirPort Sim Qt MainWindow & Dock")
    win.setCentralWidget(rad)
    win.addDockWidget(QtCore.Qt.DockWidgetArea(1), insp_dock)
    # win.resize(1000, 600)
    # win.show()
    win.showMaximized()

    # create the second view
    # second_view = radarview.PanZoomView(main_window.scene)
    # second_view.scale(0.1, -0.1)
    # second_view.show()
    # second_view.move(300, 300)

    print(simulation.SHORTCUTS)

    # enter the main loop
    app.exec_()
