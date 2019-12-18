from PyQt5 import QtWidgets
import enum
import airport


class Box(enum.Enum):
    H = True
    V = False


class AirportInspector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.named_point_widget = NamedPointInspector()
        self.taxiway_widget = TaxiwayInspector()
        self.runway_widget = RunwayInspector()
        self.object_label = QtWidgets.QLabel()

        toolbar_layout = self.create_toolbar()
        toolbar_layout.addWidget(self.object_label)

        self.root_layout = QtWidgets.QVBoxLayout(self)
        self.root_layout.addLayout(toolbar_layout)
        self.root_layout.addWidget(self.named_point_widget)  # par défaut démarre sur NamedPointInspector
        self.object_label.setText("Named point selected")
        self.named_point_widget.setVisible(True)
        self.taxiway_widget.setVisible(False)
        self.runway_widget.setVisible(False)

        self.show()

    def create_toolbar(self):
        toolbar = QtWidgets.QHBoxLayout()

        def add_menu_button(text, *args):
            button = QtWidgets.QPushButton(text)
            menu = QtWidgets.QMenu()
            for arg in args:
                menu.addAction(arg[0], arg[1])  # arg[0] = text, arg[1] = lambda function
            button.setMenu(menu)
            toolbar.addWidget(button)

        add_menu_button('Select an object',
                        ['Named point data', lambda: (self.update_widget(self.named_point_widget),
                                                      self.object_label.setText("Named point selected"))],
                        ['Taxiway data', lambda: (self.update_widget(self.taxiway_widget),
                                                  self.object_label.setText("Taxiway selected"))],
                        ['Runway data', lambda: (self.update_widget(self.runway_widget),
                                                 self.object_label.setText("Runway selected"))])
        toolbar.addStretch()
        return toolbar

    def update_widget(self, new_widget):
        widget_to_remove = self.root_layout.widget()  # Evite des erreurs si aucun des widgets est enable
        if self.named_point_widget.isVisible():
            widget_to_remove = self.named_point_widget
        elif self.taxiway_widget.isVisible():
            widget_to_remove = self.taxiway_widget
        elif self.runway_widget.isVisible():
            widget_to_remove = self.runway_widget
        widget_to_remove.setVisible(False)
        self.root_layout.replaceWidget(widget_to_remove, new_widget)
        new_widget.setVisible(True)


class Inspector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

    def create_label(self, *args):
        """arg[1] = texte dans le label
        arg[0] = nom du label"""
        label_dic = {}

        for arg in args:
            label = QtWidgets.QLabel()
            label.setText(arg[1])
            label_dic[arg[0]] = label

        return label_dic

    def create_layout(self, *args):
        """arg[0] = bool indique si H ou non H
        arg[1] = objet à mettre dans le layout"""
        root = QtWidgets.QVBoxLayout()

        for arg in args:
            if arg[0]:
                layout = QtWidgets.QHBoxLayout()
            else:
                layout = QtWidgets.QVBoxLayout()
            for widget in arg[1]:
                layout.addWidget(widget)
            root.addLayout(layout)

        root.addStretch()
        return root

    def create_menu_button(self, text, *args):
        button = QtWidgets.QPushButton(text)
        menu = QtWidgets.QMenu()
        for arg in args:
            menu.addAction(arg[0], arg[1])  # arg[0] = text, arg[1] = lambda function
        button.setMenu(menu)
        return button

    def create_button(self, text, slot):
        button = QtWidgets.QPushButton(text)
        button.clicked.connect(slot)
        return button

    def create_line_edit(self):
        line_edit = QtWidgets.QLineEdit()
        return line_edit


class NamedPointInspector(Inspector):
    def __init__(self):
        super().__init__()
        label_dic = self.create_label(['name_label', "Name"],
                                      ['type_label', "Point's type"],
                                      ['coord_label', "Point's coordinates"],
                                      ['coord_display', ""])
        name_edit = self.create_line_edit()
        type_menu = self.create_menu_button("Select a type",
                                            ["Stand", lambda type: airport.PointType.STAND],
                                            ["Deicing", lambda type: airport.PointType.DEICING],
                                            ["Runway", lambda type: airport.PointType.RUNWAY_POINT])
        # voir comment envoyer les différents parmètre à l'objet et comment récupérer les coordonnées.
        layout = self.create_layout([Box.H, (label_dic['name_label'], name_edit)],
                                    [Box.H, (label_dic['type_label'], type_menu)],
                                    [Box.H, (label_dic['coord_label'], label_dic['coord_display'])])
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.addLayout(layout)

        self.show()


class TaxiwayInspector(Inspector):
    def __init__(self):
        super().__init__()
        label_dic = self.create_label(['name_label', "Name"],
                                      ['speed_label', "Speed"],
                                      ['cat_label', "Category"],
                                      ['one_way_label', "One way"],
                                      ['coord_label', "Taxiway's coordinates"],
                                      ['coord_display', ""])
        name_edit = self.create_line_edit()
        speed_edit = self.create_line_edit()
        cat_menu = self.create_menu_button("Select a category",
                                           ["Light", lambda cat: airport.WakeVortexCategory.LIGHT],
                                           ["Medium", lambda cat: airport.WakeVortexCategory.MEDIUM],
                                           ["Heavy", lambda cat: airport.WakeVortexCategory.HEAVY])
        one_way_menu = self.create_menu_button("Select True or False",
                                               ["True", lambda one: True],
                                               ["False", lambda one: False])
        # voir comment envoyer les différents parmètre à l'objet et comment récupérer les coordonnées.
        layout = self.create_layout([Box.H, (label_dic['name_label'], name_edit)],
                                    [Box.H, (label_dic['speed_label'], speed_edit)],
                                    [Box.H, (label_dic['cat_label'], cat_menu)],
                                    [Box.H, (label_dic['one_way_label'], one_way_menu)],
                                    [Box.H, (label_dic['coord_label'], label_dic['coord_display'])])
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.addLayout(layout)

        self.show()


class RunwayInspector(Inspector):
    def __init__(self):
        super().__init__()
        label_dic = self.create_label(['name_label', "Name"],
                                      ['qfus_label', "Runway's QFUs"],
                                      ['named_points_label', "Named points"],
                                      ['coord_label', "Runway's coordinates"],
                                      ['coord_display', ""])
        name_edit = self.create_line_edit()
        qfus_edit = self.create_line_edit()
        named_points_edit = self.create_line_edit()
        # voir comment envoyer les différents parmètre à l'objet et comment récupérer les coordonnées.
        layout = self.create_layout([Box.H, (label_dic['name_label'], name_edit)],
                                    [Box.H, (label_dic['qfus_label'], qfus_edit)],
                                    [Box.H, (label_dic['named_points_label'], named_points_edit)],
                                    [Box.H, (label_dic['coord_label'], label_dic['coord_display'])])
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.addLayout(layout)

        self.show()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    inspector = AirportInspector()
    sys.exit(app.exec_())
