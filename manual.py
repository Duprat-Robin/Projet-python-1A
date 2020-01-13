from PyQt5 import QtWidgets, QtCore


class Manual(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        root_layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel()
        root_layout.addWidget(label)
        label.setText("         MANUAL        \n\n1. Input scale value in meters \n2. Set scale \n3. Set origin")
        self.setStyleSheet("color: red")
        self.show()
