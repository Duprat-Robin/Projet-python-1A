from PyQt5 import QtWidgets
import enum
import airport

INSPECTOR_WIDTH = 270

class Box(enum.Enum):
    H = True
    V = False


class AirportInspector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.named_point_widget = NamedPointInspector()
        self.taxiway_widget = TaxiwayInspector()
        self.runway_widget = RunwayInspector()
        toolbar_layout = self.create_toolbar()

        self.root_layout = QtWidgets.QVBoxLayout(self)
        self.root_layout.addLayout(toolbar_layout)
        self.root_layout.addWidget(self.named_point_widget)  # first start is on NamedPointInspector
        self.named_point_widget.setVisible(True)
        self.taxiway_widget.setVisible(False)
        self.runway_widget.setVisible(False)

        self.show()

    def create_toolbar(self):
        toolbar = QtWidgets.QHBoxLayout()

        def add_button(text, slot):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(slot)
            toolbar.addWidget(button)

        def add_menu_button(text, *args):
            button = QtWidgets.QPushButton(text)
            menu = QtWidgets.QMenu()
            for arg in args:
                menu.addAction(arg[0], arg[1])  # arg[0] = text, arg[1] = lambda function
            button.setMenu(menu)
            toolbar.addWidget(button)
            return button

        menu_object = add_menu_button('Select an object',
                                      ['Named point data', lambda: (self.update_widget(self.named_point_widget),
                                                                    menu_object.setText("Named point selected"))],
                                      ['Taxiway data', lambda: (self.update_widget(self.taxiway_widget),
                                                                menu_object.setText("Taxiway selected"))],
                                      ['Runway data', lambda: (self.update_widget(self.runway_widget),
                                                               menu_object.setText("Runway selected"))])
        add_button('Check', lambda: self.valid_data())
        toolbar.addStretch()
        return toolbar

    def update_widget(self, new_widget):
        replace = False
        widget_to_remove = self.root_layout.widget()  # Avoid errors if none widget is enable
        if self.named_point_widget.isVisible() and new_widget is not self.named_point_widget:
            widget_to_remove = self.named_point_widget
            replace = True
        elif self.taxiway_widget.isVisible() and new_widget is not self.taxiway_widget:
            widget_to_remove = self.taxiway_widget
            replace = True
        elif self.runway_widget.isVisible() and new_widget is not self.runway_widget:
            widget_to_remove = self.runway_widget
            replace = True

        if replace:
            widget_to_remove.setVisible(False)
            self.root_layout.replaceWidget(widget_to_remove, new_widget)
            new_widget.setVisible(True)

    def valid_data(self):
        if self.named_point_widget.isVisible():
            self.named_point_widget.pt_name = self.named_point_widget.name_edit.text()
            # create the object before resetting the interface end the attributes
            self.named_point_widget.reset()
        elif self.taxiway_widget.isVisible():
            self.taxiway_widget.twy_name = self.taxiway_widget.name_edit.text()
            self.taxiway_widget.twy_speed = float(self.taxiway_widget.speed_edit.text())
            # create the object before resetting the interface end the attributes
            self.taxiway_widget.reset()
        elif self.runway_widget.isVisible():
            self.runway_widget.rwy_name = self.runway_widget.name_edit.text()
            self.runway_widget.rwy_qfus = self.runway_widget.qfus_edit.text()
            self.runway_widget.rwy_named_point = self.runway_widget.named_points_edit.text()
            # create the object before resetting the interface end the attributes
            self.runway_widget.reset()
        return None


class Inspector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(INSPECTOR_WIDTH)

    def create_label(self, *args):
        """arg[1] = text in the label
        arg[0] = label's name"""
        label_dic = {}

        for arg in args:
            label = QtWidgets.QLabel()
            label.setText(arg[1])
            label_dic[arg[0]] = label

        return label_dic

    def create_layout(self, *args):
        """arg[0] = bool: Horizontal (H) or not (V)
        arg[1] = object to set in the layout"""
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
        self.pt_name = ""
        self.pt_type = None  # None | PointType

        label_dic = self.create_label(['name_label', "Name"],
                                      ['type_label', "Point's type"],
                                      ['coord_label', "Point's coordinates"],
                                      ['coord_display', ""])
        self.name_edit = self.create_line_edit()
        self.type_menu = self.create_menu_button("Select a type",
                                            ["Stand", lambda: (self.set_point_type(airport.PointType.STAND),
                                                               self.type_menu.setText("Stand"))],
                                            ["Deicing", lambda: (self.set_point_type(airport.PointType.DEICING),
                                                                 self.type_menu.setText("Deicing"))],
                                            ["Runway", lambda: (self.set_point_type(airport.PointType.RUNWAY_POINT),
                                                                self.type_menu.setText("Runway"))])
        # voir comment envoyer les différents parmètre à l'objet et comment récupérer les coordonnées.
        layout = self.create_layout([Box.H, (label_dic['name_label'], self.name_edit)],
                                    [Box.H, (label_dic['type_label'], self.type_menu)],
                                    [Box.H, (label_dic['coord_label'], label_dic['coord_display'])])
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.addLayout(layout)

        self.show()

    def set_point_type(self, pt_type):
        self.pt_type = pt_type

    def reset(self):
        self.pt_name = ""
        self.pt_type = None
        self.name_edit.clear()
        self.type_menu.setText("Select a type")


class TaxiwayInspector(Inspector):
    def __init__(self):
        super().__init__()
        self.twy_name = ""
        self.twy_speed = 0
        self.twy_cat = None  # None | WakeVortexCategory
        self.twy_one_way = None  # None | bool

        label_dic = self.create_label(['name_label', "Name"],
                                      ['speed_label', "Speed"],
                                      ['cat_label', "Category"],
                                      ['one_way_label', "One way"],
                                      ['coord_label', "Taxiway's coordinates"],
                                      ['coord_display', ""])
        self.name_edit = self.create_line_edit()
        self.speed_edit = self.create_line_edit()
        self.cat_menu = self.create_menu_button("Select a category",
                                           ["Light", lambda: (self.update_cat(airport.WakeVortexCategory.LIGHT),
                                                              self.cat_menu.setText("Light"))],
                                           ["Medium", lambda: (self.update_cat(airport.WakeVortexCategory.MEDIUM),
                                                               self.cat_menu.setText("Medium"))],
                                           ["Heavy", lambda: (self.update_cat(airport.WakeVortexCategory.HEAVY),
                                                              self.cat_menu.setText("Heavy"))])
        self.one_way_menu = self.create_menu_button("Select True or False",
                                               ["True", lambda: (self.update_one_way(True),
                                                                 self.one_way_menu.setText("True"))],
                                               ["False", lambda: (self.update_one_way(False),
                                                                  self.one_way_menu.setText("False"))])
        # voir comment envoyer les différents parmètre à l'objet et comment récupérer les coordonnées.
        layout = self.create_layout([Box.H, (label_dic['name_label'], self.name_edit)],
                                    [Box.H, (label_dic['speed_label'], self.speed_edit)],
                                    [Box.H, (label_dic['cat_label'], self.cat_menu)],
                                    [Box.H, (label_dic['one_way_label'], self.one_way_menu)],
                                    [Box.H, (label_dic['coord_label'], label_dic['coord_display'])])
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.addLayout(layout)

        self.show()

    def update_cat(self, cat):
        self.twy_cat = cat

    def update_one_way(self, one_way):
        self.twy_one_way = one_way

    def reset(self):
        self.twy_name = ""
        self.twy_speed = 0
        self.twy_cat = None
        self.twy_one_way = None
        self.name_edit.clear()
        self.speed_edit.clear()
        self.cat_menu.setText("Select a category")
        self.one_way_menu.setText("Select True or False")


class RunwayInspector(Inspector):
    def __init__(self):
        super().__init__()
        self.rwy_name = ""
        self.rwy_qfus = ""  # type à vérifier
        self.rwy_named_point = ""  # type à vérifier

        label_dic = self.create_label(['name_label', "Name"],
                                      ['qfus_label', "Runway's QFUs"],
                                      ['named_points_label', "Named points"],
                                      ['coord_label', "Runway's coordinates"],
                                      ['coord_display', ""])
        self.name_edit = self.create_line_edit()
        self.qfus_edit = self.create_line_edit()
        self.named_points_edit = self.create_line_edit()
        # voir comment envoyer les différents parmètre à l'objet et comment récupérer les coordonnées.
        layout = self.create_layout([Box.H, (label_dic['name_label'], self.name_edit)],
                                    [Box.H, (label_dic['qfus_label'], self.qfus_edit)],
                                    [Box.H, (label_dic['named_points_label'], self.named_points_edit)],
                                    [Box.H, (label_dic['coord_label'], label_dic['coord_display'])])
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.addLayout(layout)

        self.show()

    def reset(self):
        self.rwy_name = ""
        self.rwy_qfus = ""
        self.rwy_named_point = ""
        self.name_edit.clear()
        self.qfus_edit.clear()
        self.named_points_edit.clear()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    inspector = AirportInspector()
    sys.exit(app.exec_())
