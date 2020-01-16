from PyQt5 import QtWidgets
import enum
import airport, file_airport, geometry, manual

INSPECTOR_WIDTH = 270


class Box(enum.Enum):
    H = True
    V = False


class AirportInspector(QtWidgets.QWidget):

    def __init__(self, the_draw):
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
        manual_disp = manual.Manual()
        self.root_layout.addWidget(manual_disp)

        self.draw = the_draw
        self.list_coordinates = []
        self.draw.signal.ask_inspection_signal.connect(self.emit_signal)
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
        add_button('OK', lambda: self.valid_data())
        toolbar.addStretch()
        return toolbar

    def emit_signal(self):
        item = self.draw.highlighted_item
        self.list_coordinates = []
        if type(item) is QtWidgets.QGraphicsEllipseItem:
            coordinates = self.draw.airport_items_dict[item]
            coordinates_meters = self.draw.scale_configuration.scene_to_meters(coordinates)
            self.list_coordinates.append((int(coordinates_meters.x()), int(coordinates_meters.y())))
            self.named_point_widget.label_dic['coord_display'].setText("({0:.0f}, {1:.0f})".format(coordinates_meters.x(), coordinates_meters.y()))
        else:
            list_coordinates_str = []
            for elmt in self.draw.airport_items_dict[item]:
                coordinates_meters = self.draw.scale_configuration.scene_to_meters(elmt[1])
                self.list_coordinates.append((int(coordinates_meters.x()), int(coordinates_meters.y())))
                list_coordinates_str.append("({0:.0f}, {1:.0f})".format(coordinates_meters.x(), coordinates_meters.y()))
            if self.taxiway_widget.isVisible():
                self.taxiway_widget.label_dic['coord_display'].setText("\n".join(list_coordinates_str))
            else:
                self.runway_widget.label_dic['coord_display'].setText("\n".join(list_coordinates_str))

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
        """In NamedPoint class, Taxiway class and Runway class, coordinates of points and items
        must have a specific format to be understood by the program"""
        if self.named_point_widget.isVisible():
            self.named_point_widget.pt_name = self.named_point_widget.name_edit.text()
            point = "{0[0]},{0[1]}".format(self.list_coordinates[0])
            named_point = airport.NamedPoint(self.named_point_widget.pt_name, self.named_point_widget.pt_type, point)
            self.draw.airport_file.airport.points.append(named_point)
            self.draw.airport_file.airport.pt_dict[named_point.name] = named_point
            self.named_point_widget.reset()

        elif self.taxiway_widget.isVisible():
            self.taxiway_widget.twy_name = self.taxiway_widget.name_edit.text()

            self.taxiway_widget.twy_speed = int(self.taxiway_widget.speed_edit.text())
            coord_str = file_airport.tuple_to_str(self.list_coordinates)
            coord = file_airport.xys_to_points(coord_str.split())

            taxiway = airport.Taxiway(self.taxiway_widget.twy_name, self.taxiway_widget.twy_speed,
                                      self.taxiway_widget.twy_cat, self.taxiway_widget.twy_one_way, coord)
            self.draw.airport_file.airport.taxiways.append(taxiway)
            self.taxiway_widget.reset()
        elif self.runway_widget.isVisible():
            self.runway_widget.rwy_name = self.runway_widget.name_edit.text()
            self.runway_widget.rwy_qfus = self.runway_widget.qfus_edit.text().split('-')
            self.runway_widget.rwy_named_point = self.runway_widget.named_points_edit.text()
            ends = tuple(geometry.Point(i[0], i[1]) for i in self.list_coordinates)
            runway = airport.Runway(self.runway_widget.rwy_name, self.runway_widget.rwy_qfus[0],
                                    self.runway_widget.rwy_qfus[1], ends, self.runway_widget.rwy_named_point)
            self.draw.airport_file.airport.runways.append(runway)
            self.draw.airport_file.airport.qfu_dict[runway.qfus[0]] = runway
            self.draw.airport_file.airport.qfu_dict[runway.qfus[1]] = runway
            self.runway_widget.reset()


class Inspector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(INSPECTOR_WIDTH)  # Inspector's Width is fixed

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

        self.label_dic = self.create_label(['name_label', "Name"],
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

        layout = self.create_layout([Box.H, (self.label_dic['name_label'], self.name_edit)],
                                    [Box.H, (self.label_dic['type_label'], self.type_menu)],
                                    [Box.H, (self.label_dic['coord_label'], self.label_dic['coord_display'])])
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.addLayout(layout)

        self.show()

    def set_point_type(self, pt_type):
        self.pt_type = pt_type

    def reset(self):
        self.pt_name = ""
        self.pt_type = None
        self.name_edit.clear()


class TaxiwayInspector(Inspector):
    def __init__(self):
        super().__init__()
        self.twy_name = ""
        self.twy_speed = 10
        self.twy_cat = None  # None | WakeVortexCategory
        self.twy_one_way = False

        self.label_dic = self.create_label(['name_label', "Name"],
                                      ['speed_label', "Speed"],
                                      ['cat_label', "Category"],
                                      ['one_way_label', "One way"],
                                      ['coord_label', "Taxiway's coordinates"],
                                      ['coord_display', ""])
        self.name_edit = self.create_line_edit()
        self.speed_edit = self.create_line_edit()
        self.speed_edit.setText(str(self.twy_speed))
        self.cat_menu = self.create_menu_button("Select a category",
                                           ["Light", lambda: (self.update_cat(airport.WakeVortexCategory.LIGHT),
                                                              self.cat_menu.setText("Light"))],
                                           ["Medium", lambda: (self.update_cat(airport.WakeVortexCategory.MEDIUM),
                                                               self.cat_menu.setText("Medium"))],
                                           ["Heavy", lambda: (self.update_cat(airport.WakeVortexCategory.HEAVY),
                                                              self.cat_menu.setText("Heavy"))])
        self.one_way_menu = self.create_menu_button("False",
                                               ["True", lambda: (self.update_one_way(True),
                                                                 self.one_way_menu.setText("True"))],
                                               ["False", lambda: (self.update_one_way(False),
                                                                  self.one_way_menu.setText("False"))])

        layout = self.create_layout([Box.H, (self.label_dic['name_label'], self.name_edit)],
                                    [Box.H, (self.label_dic['speed_label'], self.speed_edit)],
                                    [Box.H, (self.label_dic['cat_label'], self.cat_menu)],
                                    [Box.H, (self.label_dic['one_way_label'], self.one_way_menu)],
                                    [Box.H, (self.label_dic['coord_label'], self.label_dic['coord_display'])])
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.addLayout(layout)

        self.show()

    def update_cat(self, cat):
        self.twy_cat = cat

    def update_one_way(self, one_way):
        self.twy_one_way = one_way

    def reset(self):
        self.twy_name = ""
        self.twy_speed = 10
        self.twy_cat = None
        self.twy_one_way = False
        self.name_edit.clear()
        self.speed_edit.setText(str(self.twy_speed))


class RunwayInspector(Inspector):
    def __init__(self):
        super().__init__()
        self.rwy_name = ""
        self.rwy_qfus = ""  # type à vérifier
        self.rwy_named_point = ""  # type à vérifier

        self.label_dic = self.create_label(['name_label', "Name"],
                                      ['qfus_label', "Runway's QFUs"],
                                      ['named_points_label', "Named points"],
                                      ['coord_label', "Runway's coordinates"],
                                      ['coord_display', ""])
        self.name_edit = self.create_line_edit()
        self.qfus_edit = self.create_line_edit()
        self.named_points_edit = self.create_line_edit()

        layout = self.create_layout([Box.H, (self.label_dic['name_label'], self.name_edit)],
                                    [Box.H, (self.label_dic['qfus_label'], self.qfus_edit)],
                                    [Box.H, (self.label_dic['named_points_label'], self.named_points_edit)],
                                    [Box.H, (self.label_dic['coord_label'], self.label_dic['coord_display'])])
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
