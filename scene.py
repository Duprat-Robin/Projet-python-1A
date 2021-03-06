from PyQt5 import QtWidgets, QtGui, QtCore
import math
import file_airport, geometry


ORIGINE_X, ORIGINE_Y = 0, 0
ZOOM_FACTOR = 1.1
RATIO = 0.9
ARROW, CROSS = 0, 2


class GraphicsZoom(QtWidgets.QGraphicsView):
    """Control of the application's zoom"""
    def __init__(self, scene):
        super().__init__(scene)
        # enable anti-aliasing
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        # enable drag and drop of the view
        self.setDragMode(self.ScrollHandDrag)
        self.origin_zoom = 0

    def wheelEvent(self, event):
        """Overrides method in QGraphicsView in order to zoom it when mouse scroll occurs"""
        factor = math.pow(1.001, event.angleDelta().y())
        self.zoom_view(factor)

    def zoom_view(self, factor):
        """Updates the zoom factor of the view"""
        self.origin_zoom = self.cursor().pos()
        self.setTransformationAnchor(self.AnchorUnderMouse)
        super().scale(factor, factor)


class GraphicsScale(QtWidgets.QWidget):
    """Define scale factor and origin's position"""
    def __init__(self, widget):
        super().__init__(widget)
        self.widget = widget
        self.origin_set = False
        self.origin_pos = QtCore.QPointF(0, 0)
        self.scale_set = False
        self.scale_point = 0
        self.scale_factor = 1
        self.start_pos, self.end_pos = 0, 0
        self.entry_meters = QtWidgets.QLineEdit("m")
        self.meters_value = 1
        self.nbr_pixels = 1

    def setScale(self):
        if self.scale_point == 0:
            self.start_pos = self.widget.get_coordinates_scene()
        elif self.scale_point == 1:
            self.end_pos = self.widget.get_coordinates_scene()
            self.nbr_pixels = self.distance(self.start_pos, self.end_pos)
        self.scale_point += 1
        if self.scale_point == 2:
            self.scale_set = False
            self.scale_factor = self.nbr_pixels / self.meters_value
            self.widget.airport_file.airport.factor = (self.nbr_pixels, self.meters_value, self.scale_factor)
            self.entry_meters.setText("scale factor = {0.nbr_pixels:.3f}/{0.meters_value} = {0.scale_factor:.3f} scene_units/m".format(self))

    def enable_scale_set(self):
        """Enable scale configuration"""
        self.scale_set = True

    def setOrigin(self):
        """Origin in scene coordinates"""
        self.origin_pos = self.widget.get_coordinates_scene()
        self.widget.airport_file.airport.origin = self.origin_pos
        self.origin_set = False

    def enable_origin_set(self):
        """Enable origin configuration"""
        self.origin_set = True

    def distance(self, qpoint1, qpoint2):
        """Convert QPoint in geometry Point and compute"""
        point1 = geometry.Point(qpoint1.x(), qpoint1.y())
        point2 = geometry.Point(qpoint2.x(), qpoint2.y())
        return point1.distance(point2)

    def screen_to_map(self, temp_origin):
        """find the point on the map from its screen position"""
        current_cursor_pos_screen = super().cursor().pos()
        current_cursor_pos_map = ZOOM_FACTOR * factor * self.distance(current_cursor_pos_screen, temp_origin)
        return current_cursor_pos_map

    def edit_meters(self):
        self.meters_value = float(self.entry_meters.text()[:-1])
        self.entry_meters.clearFocus()

    def scene_to_meters(self, qpoint):
        x_meter = (qpoint.x()-self.origin_pos.x())/self.scale_factor
        y_meter = (self.origin_pos.y()-qpoint.y())/self.scale_factor
        return QtCore.QPointF(x_meter, y_meter)

    def meters_to_scene(self, qpoint):
        x_scene = self.origin_pos.x() + qpoint.x()*self.scale_factor
        y_scene = self.origin_pos.y() - qpoint.y()*self.scale_factor
        return QtCore.QPointF(x_scene, y_scene)

    def open_scale_origin(self):
        """"Get scale factor and origin's position from an open file"""
        self.nbr_pixels, self.meters_value, self.scale_factor = self.widget.airport_file.airport.factor
        self.origin_pos = self.widget.airport_file.airport.origin


class GraphicsWidget(QtWidgets.QWidget):
    """Lead the interface and the toolbar"""
    def __init__(self):
        super().__init__()

        self.image = QtGui.QPixmap()
        self.setMouseTracking(True)
        self.airport_file = file_airport.FileAirport()

        self.scene = QtWidgets.QGraphicsScene()
        self.view = GraphicsZoom(self.scene)
        self.scale_configuration = GraphicsScale(self)

        root_layout = QtWidgets.QVBoxLayout(self)
        toolbar = self.create_toolbar()
        root_layout.addLayout(toolbar)
        root_layout.addWidget(self.view)

        screen = QtWidgets.QDesktopWidget()
        size_screen = screen.screenGeometry(screen.screenNumber(self))  # Initial window width (pixels) Initial window height (pixels)

        self.view.fitInView(self.view.sceneRect(), QtCore.Qt.KeepAspectRatio)
        old_height_screen = self.size().height()
        self.resize(size_screen.width(), size_screen.height())
        self.view.zoom_view(size_screen.height() * RATIO / old_height_screen)

        self.airport_file.image_signal.ask_image_signal.connect(self.open_repository_image)

        self.showMaximized()

    def get_coordinates_scene(self):
        pos_cursor = self.cursor().pos()
        pos_cursor_view = self.view.mapFromGlobal(pos_cursor)
        pos_cursor_scene = self.view.mapToScene(pos_cursor_view)
        return pos_cursor_scene

    def open_image(self):
        """Get the repository of the image through a Dialog Box"""
        repository = QtWidgets.QFileDialog()
        self.airport_file.image_repository = str(repository.getOpenFileName()[0])
        self.open_repository_image(self.airport_file.image_repository)

    def open_repository_image(self, repository):
        """Open the image from a specific repository"""
        self.image.load(repository)
        self.scene.addPixmap(self.image)

        screen = QtWidgets.QDesktopWidget()
        size_screen = screen.screenGeometry(screen.screenNumber(self))
        self.view.fitInView(self.view.sceneRect(), QtCore.Qt.KeepAspectRatio)
        old_height_screen = self.size().height()
        self.view.zoom_view(size_screen.height() * RATIO / old_height_screen)

    def create_toolbar(self):
        toolbar = QtWidgets.QVBoxLayout()
        upper_toolbar = QtWidgets.QHBoxLayout()
        lower_toolbar = QtWidgets.QHBoxLayout()

        def add_button(text, slot):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(slot)
            upper_toolbar.addWidget(button)

        def add_menu_button(text, *args):
            button = QtWidgets.QPushButton(text)
            menu = QtWidgets.QMenu()
            for arg in args:
                menu.addAction(arg[0], arg[1])  # arg[0] = text, arg[1] = lambda function
            button.setMenu(menu)
            upper_toolbar.addWidget(button)

        add_menu_button('File', ['New File', lambda: self.airport_file.newFile()],
                        ['Open File', lambda: (self.airport_file.openFile(), self.scale_configuration.open_scale_origin(),
                                               self.draw_airport_points())],
                        ['Save', lambda: self.airport_file.saveFile()],
                        ['Save As', lambda: self.airport_file.saveAsFile()],
                        ['Open Image', lambda: self.open_image()])

        add_button('-', lambda: self.view.zoom_view(1 / ZOOM_FACTOR))
        add_button('+', lambda: self.view.zoom_view(ZOOM_FACTOR))
        add_button('Default mode', lambda: (self.cursor_mode_reset(), cursor_set_default(self),
                                            self.view.setDragMode(self.view.NoDrag)))
        add_button('Zoom and drag', lambda: drag_mod(self))
        add_button('Set scale', lambda: (self.cursor_mode_point(),  cursor_set_draw(self),
                                         self.scale_configuration.enable_scale_set()))
        add_button('Set origin', lambda: (self.cursor_mode_point(),  cursor_set_draw(self),
                                          self.scale_configuration.enable_origin_set()))

        add_button('Draw point', lambda: (self.cursor_mode_point(), cursor_set_draw(self)))
        add_button('Draw line', lambda: (self.cursor_mode_line(), cursor_set_draw(self)))
        add_button('Delete', lambda: (self.cursor_deleting_mode(), cursor_set_default(self)))

        airport_name_label = QtWidgets.QLabel()
        airport_name_label.setText("Airport's name:")
        scale_edit_label = QtWidgets.QLabel()
        scale_edit_label.setText("Scale editor:")

        lower_toolbar.addWidget(scale_edit_label)
        lower_toolbar.addWidget(self.scale_configuration.entry_meters)
        lower_toolbar.addWidget(airport_name_label)
        lower_toolbar.addWidget(self.airport_file.airport.airport_name_edit)

        self.scale_configuration.entry_meters.editingFinished.connect(self.scale_configuration.edit_meters)
        self.airport_file.airport.airport_name_edit.editingFinished.connect(self.airport_file.airport.update_airport_name)

        upper_toolbar.addStretch()
        lower_toolbar.addStretch()
        toolbar.addLayout(upper_toolbar)
        toolbar.addLayout(lower_toolbar)

        def add_shortcut(text, slot):
            """creates an application-wide key binding"""
            shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(text), self)
            shortcut.activated.connect(slot)

        add_shortcut('-', lambda: self.view.zoom_view(1/ZOOM_FACTOR))
        add_shortcut('+', lambda: self.view.zoom_view(ZOOM_FACTOR))
        return toolbar


def cursor_set_default(widget):
    arrow_cursor = QtGui.QCursor()
    arrow_cursor.setShape(ARROW)
    widget.setCursor(arrow_cursor)


def cursor_set_draw(widget):
    widget.view.setDragMode(False)
    cross_cursor = QtGui.QCursor()
    cross_cursor.setShape(CROSS)
    widget.setCursor(cross_cursor)


def drag_mod(widget):
    if widget.view.dragMode() == widget.view.NoDrag:
        arrow_cursor = QtGui.QCursor()
        arrow_cursor.setShape(ARROW)
        widget.setCursor(arrow_cursor)
        widget.view.setDragMode(widget.view.ScrollHandDrag)
    else:
        widget.view.setDragMode(widget.view.NoDrag)
    widget.cursor_mode_reset()

