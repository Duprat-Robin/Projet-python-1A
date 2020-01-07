from PyQt5 import QtWidgets, QtGui, QtCore
import sys, math
import airport, file_airport, geometry


ORIGINE_X, ORIGINE_Y = 0, 0
ZOOM_FACTOR = 1.1
RATIO = 0.9
IMAGE_FILE = "lfbo_adc.jpg"
ARROW, CROSS = 0, 2


class GraphicsZoom(QtWidgets.QGraphicsView):
    """Contrôle le zoom de l'application"""
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
        self.origin_zoom = self.cursor().pos()  # ap zoom av clic
        self.setTransformationAnchor(self.AnchorUnderMouse)
        super().scale(factor, factor)


class GraphicsScale(QtWidgets.QWidget):
    """Définition de l'échelle pour passer des coordonnées métriques de la réalité aux pixel de l'écran"""
    def __init__(self, widget):
        """L'objet possède les attributs et les méthodes de notre scene (pour les appeller, utiliser super()."""
        super().__init__(widget)
        self.scale_set = False
        self.scale_point = 0
        self.scale_factor = 0  # en pixel/m
        self.start_pos, self.end_pos = 0, 0
        self.entry_meters = QtWidgets.QLineEdit()
        self.meters_value = 0
        self.nbr_pixels = 0

    def setScale(self):
        """Création de l'échelle dans un QLineEdit"""
        if self.scale_point == 0:
            self.start_pos = super().cursor().pos()
        else:
            self.scale_set = False
            self.end_pos = super().cursor().pos()
            self.nbr_pixels = self.distance(self.start_pos, self.end_pos)
            self.scale_factor = self.nbr_pixels / self.meters_value
            self.entry_meters.setText("scale factor = {0.nbr_pixels}/{0.meters_value} = {0.scale_factor} pxl/m".format(self))
        self.scale_point += 1

    def enable_scale_set(self):
        """Active la configuration du zoom"""
        self.scale_set = True

    def distance(self, qpoint1, qpoint2):
        """Prend des QPoint en paramètres et utilise les méthodes de geometry pour faire les calculs"""
        point1 = geometry.Point(qpoint1.x(), qpoint1.y())
        point2 = geometry.Point(qpoint2.x(), qpoint2.y())
        return point1.distance(point2)

    def screen_to_map(self, temp_origin):
        """retrouve la position par rapport à la carte d'un point de l'écran """
        current_cursor_pos_screen = super().cursor().pos()
        current_cursor_pos_map = ZOOM_FACTOR * factor * self.distance(current_cursor_pos_screen, temp_origin)
        return current_cursor_pos_map

    def edit_meters(self):
            self.meters_value = float(self.entry_meters.text()[:-1])
            self.entry_meters.clearFocus()


class GraphicsWidget(QtWidgets.QWidget):
    """Gère l'affichage des éléments de bases et des barres d'outils"""
    def __init__(self):
        super().__init__()

        self.image = QtGui.QPixmap()
        self.image.load(IMAGE_FILE)
        self.setMouseTracking(True)
        self.airport = file_airport.FileAirport()

        self.scene = QtWidgets.QGraphicsScene()
        self.view = GraphicsZoom(self.scene)
        self.scale_configuration = GraphicsScale(self)

        self.scene.addPixmap(self.image)

        root_layout = QtWidgets.QVBoxLayout(self)  # modifie la taille initiale de l'affichage
        toolbar = self.create_toolbar()
        root_layout.addLayout(toolbar)
        root_layout.addWidget(self.view)  # l'image étant en fond d'écan, n'apparait pas dans le layout

        screen = QtWidgets.QDesktopWidget()
        size_screen = screen.screenGeometry(screen.screenNumber(self))  # Initial window width (pixels) Initial window height (pixels)

        self.view.fitInView(self.view.sceneRect(), QtCore.Qt.KeepAspectRatio)
        old_height_screen = self.size().height()
        self.resize(size_screen.width(), size_screen.height())
        self.view.zoom_view(size_screen.height() * RATIO / old_height_screen)

        self.showMaximized()

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

        add_menu_button('File', ['New File', lambda: self.airport.newFile()],
                        ['Open File', lambda: self.airport.openFile()],
                        ['Save', lambda: self.airport.saveFile()],
                        ['Save As', lambda: self.airport.saveAsFile()])

        add_button('-', lambda: self.view.zoom_view(1 / ZOOM_FACTOR))
        add_button('+', lambda: self.view.zoom_view(ZOOM_FACTOR))
        add_button('Default mode', lambda: (cursor_set(self), self.view.setDragMode(False)))
        add_button('Zoom and drag', lambda: drag_mod(self))
        add_button('Set scale', lambda: self.scale_configuration.enable_scale_set())
        add_button('Draw point', lambda: (self.drawing_mode_point(), cursor_set(self, False)))
        add_button('Draw line', lambda: (self.drawing_mode_line(), cursor_set(self, False)))
        add_button('Delete', lambda: self.deleting_mode())

        toolbar.addWidget(self.scale_configuration.entry_meters)
        self.scale_configuration.entry_meters.editingFinished.connect(self.scale_configuration.edit_meters)
        toolbar.addStretch()

        def add_shortcut(text, slot):
            """creates an application-wide key binding"""
            shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(text), self)
            shortcut.activated.connect(slot)

        add_shortcut('-', lambda: self.view.zoom_view(1/ZOOM_FACTOR))
        add_shortcut('+', lambda: self.view.zoom_view(ZOOM_FACTOR))
        return toolbar


def cursor_set(widget, set_arrow = True):
    cross_cursor = QtGui.QCursor()
    cross_cursor.setShape(CROSS)
    arrow_cursor = QtGui.QCursor()
    arrow_cursor.setShape(ARROW)

    if not set_arrow:
        widget.setCursor(cross_cursor)
        widget.view.setDragMode(False)
    else:
        widget.setCursor(arrow_cursor)
        widget.cursor_mode_reset()


def drag_mod(widget):
    if widget.view.dragMode() == widget.view.NoDrag:
        arrow_cursor = QtGui.QCursor()
        arrow_cursor.setShape(ARROW)
        widget.setCursor(arrow_cursor)
        widget.view.setDragMode(widget.view.ScrollHandDrag)
    else:
        widget.view.setDragMode(widget.view.NoDrag)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Scene = GraphicsWidget()
    sys.exit(app.exec_())
