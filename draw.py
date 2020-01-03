from PyQt5 import QtWidgets, QtGui, QtCore
import sys, enum
import scene, airport, file_airport


POINT_Z_VALUE = 1
WAY_Z_VALUE = 0
AIRPORT_FILE = ""


class Mode(enum.Enum):
    """0: default mode (draw disable) 1: draw points 2: draw lines 3: erase items"""
    DEFAULT = 0
    DRAW_POINT = 1
    DRAW_LINE = 2
    DELETE = 3


class DrawAirport(scene.GraphicsWidget):
    def __init__(self):
        super().__init__()
        self.cursor_mode = Mode.DEFAULT
        self.line_point_list = []
        self.on_item = False
        self.current_item = None

    def mousePressEvent(self, event):
        if (self.cursor_mode == Mode.DRAW_POINT or self.cursor_mode == Mode.DRAW_LINE) and not self.on_item:
            self.draw_point()
        if self.cursor_mode == Mode.DELETE:
            self.delete()
        self.view.update()
        if self.on_item:
            print(self.current_item)

    def mouseDoubleClickEvent(self, event):
        if self.cursor_mode == Mode.DRAW_LINE and len(self.line_point_list) != 0:
            self.draw_line()
            self.line_point_list = []
        self.view.update()

    def cursor_mode_reset(self):
        self.cursor_mode = Mode.DEFAULT

    def cursor_mode_point(self):
        self.cursor_mode = Mode.DRAW_POINT

    def cursor_mode_line(self):
        self.cursor_mode = Mode.DRAW_LINE

    def cursor_deleting_mode(self):
        self.cursor_mode = Mode.DELETE

    def draw_point(self):
        width = 20
        color = QtGui.QColor(255, 0, 0)
        if self.scale_configuration.scale_set:
            color = QtGui.QColor(0, 0, 255)
            self.scale_configuration.setScale()
        pos_cursor_scene = self.get_coordonates_scene()
        coor_point = QtCore.QRectF(pos_cursor_scene.x() - width / 2, pos_cursor_scene.y() - width / 2, width, width)
        point = QtWidgets.QGraphicsEllipseItem(coor_point)
        point.setBrush(QtGui.QBrush(color))
        setHighlight(point, self)
        self.scene.addItem(point)
        if self.cursor_mode == Mode.DRAW_LINE:
            self.line_point_list.append(pos_cursor_scene)

    def draw_line(self):
        width = 10
        color = QtGui.QColor(0, 255, 0)
        path = QtGui.QPainterPath()
        path.moveTo(self.line_point_list[0].x(), self.line_point_list[0].y())
        for point in self.line_point_list[1:]:
            path.lineTo(point.x(), point.y())
        line = QtWidgets.QGraphicsPathItem(path)
        setHighlight(line,self)
        self.scene.addItem(line)

        # line.setPen(pen)

    def delete(self):
        self.scene.removeItem(self.current_item)
        self.on_item = False
        self.view.update()  # met à jour la vue

    def get_coordonates_scene(self):
        pos_cursor = self.cursor().pos()
        print(pos_cursor)
        pos_cursor_view = self.view.mapFromGlobal(pos_cursor)
        print(pos_cursor_view)
        pos_cursor_scene = self.view.mapToScene(pos_cursor_view)
        print(pos_cursor_scene)
        return (pos_cursor_scene)

    def draw_airport_points(self, airport):
        """Ne fonctionne pas encore!!!"""
        points_group = QtWidgets.QGraphicsItemGroup()
        self.scene.addItem(points_group)
        points_group.setZValue(POINT_Z_VALUE)

        pen = QtGui.QPen(QtCore.Qt.transparent)
        width = 0.7 * SEP  # ajouter ce paramètre de séparation minimale dans airport as attribut?
        dw = width / 2.
        for point in apt.points:
            bounds = QtCore.QRectF(point.x - dw, point.y - dw, width, width)
            if point.type == airport.PointType.STAND:
                item = QtWidgets.QGraphicsEllipseItem(bounds, points_group)
                item.setBrush(STAND_BRUSH)
                point_type_description = "Stand"
            else:
                item = QtWidgets.QGraphicsRectItem(bounds, points_group)
                item.setBrush(POINT_BRUSH)
                if point.type == airport.PointType.RUNWAY_POINT:
                    point_type_description = "Runway point"
                else:
                    point_type_description = "Deicing point"
            item.setPen(pen)
            item.setToolTip(point_type_description + ' ' + point.name)


def highlight(item,scene):
    item.setPen(QtGui.QPen(item.pen().color(), item.pen().width() + 2))
    scene.on_item = True
    scene.current_item = item


def unhighlight(item,scene):
    item.setPen(QtGui.QPen(item.pen().color(), item.pen().width() - 2))
    scene.on_item = False
    scene.current_item = None


def setHighlight(item,scene):
    item.setAcceptHoverEvents(True)
    item.hoverEnterEvent = lambda event: highlight(item,scene)
    item.hoverLeaveEvent = lambda event: unhighlight(item,scene)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Scene = DrawAirport()
    sys.exit(app.exec_())
