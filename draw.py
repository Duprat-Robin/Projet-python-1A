from PyQt5 import QtWidgets, QtGui, QtCore
import sys, enum
import scene


POINT_Z_VALUE = 1
WAY_Z_VALUE = 0
AIRPORT_FILE = ""


class Mode(enum.Enum):
    """0: default mode (draw disable) 1: draw points 2: draw lines 3: erase items"""
    DEFAULT = 0
    DRAW_POINT = 1
    DRAW_LINE = 2
    DELETE = 3


class InspectorSignal(QtCore.QObject):
    ask_inspection_signal = QtCore.pyqtSignal()


class DrawAirport(scene.GraphicsWidget):

    def __init__(self):
        super().__init__()
        self.airport_items_dict = self.airport_file.airport.items_dict
        self.cursor_mode = Mode.DEFAULT
        self.line_point_list = []
        self.on_item = False
        self.current_item = None  # None | Current item under the cursor
        self.clicked_item = None  # None | Last clicked item
        self.highlighted_item = None  # None | Highlighted item when was a clicked_item
        self.signal = InspectorSignal()

    def mousePressEvent(self, event):
        if self.cursor_mode == Mode.DRAW_POINT or self.cursor_mode == Mode.DRAW_LINE :
            self.draw_point()
        if self.cursor_mode == Mode.DELETE:
            self.delete()
        if self.cursor_mode == Mode.DEFAULT:
            if self.on_item:
                self.clicked_item = self.current_item
                if self.highlighted_item is not None and self.clicked_item is not self.highlighted_item:
                    unhighlight(self.highlighted_item, self)
                    self.highlighted_item = None
                highlight(self.clicked_item, self)
                self.highlighted_item = self.clicked_item
                self.signal.ask_inspection_signal.emit()
            elif self.highlighted_item is not None:
                unhighlight(self.highlighted_item, self)
                self.highlighted_item = None
        self.view.update()

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

    def draw_point_coord(self, x, y, width, color):
        coor_point = QtCore.QRectF(x - width / 2, y - width / 2, width, width)
        ellipse = QtWidgets.QGraphicsEllipseItem(coor_point)
        ellipse.setBrush(QtGui.QBrush(color))
        setHighlight(ellipse, self)
        self.scene.addItem(ellipse)
        return ellipse

    def draw_point(self):
        if not self.on_item:
            width = 20
            color = QtGui.QColor(255, 0, 0)
            if self.scale_configuration.scale_set:
                color = QtGui.QColor(0, 0, 255)
                self.scale_configuration.setScale()
            if self.scale_configuration.origin_set:
                color = QtGui.QColor(0, 0, 255)
                self.scale_configuration.setOrigin()
            pos_cursor_scene = self.get_coordinates_scene()  # ??? scale configuration
            point = self.draw_point_coord(pos_cursor_scene.x(), pos_cursor_scene.y(), width, color)
            self.airport_items_dict[point] = pos_cursor_scene
            if self.cursor_mode == Mode.DRAW_LINE:
                self.line_point_list.append((point, pos_cursor_scene))
        if self.on_item:
            self.line_point_list.append((self.current_item, self.airport_items_dict[self.current_item]))
        # print("test", pos_cursor_scene, self.scale_configuration.meters_to_scene(self.scale_configuration.scene_to_meters(pos_cursor_scene)))

    def draw_line(self):
        width = 10
        color = QtGui.QColor(0, 255, 0)
        path = QtGui.QPainterPath()
        path.moveTo(self.line_point_list[0][1].x(), self.line_point_list[0][1].y())
        for point in self.line_point_list[1:]:
            path.lineTo(point[1].x(), point[1].y())
        line = QtWidgets.QGraphicsPathItem(path)
        setHighlight(line, self)
        self.scene.addItem(line)
        self.airport_items_dict[line] = self.line_point_list

        # line.setPen(pen)

    def delete(self):
        self.scene.removeItem(self.current_item)
        self.on_item = False

    def draw_airport_points(self):
        apt = self.airport_file.airport
        width = 20
        color = QtGui.QColor(255, 0, 0)

        # NamedPoint
        for point in apt.points:
            pointF = self.scale_configuration.meters_to_scene(QtCore.QPointF(point.x, point.y))
            x, y = pointF.x(), pointF.y()
            ellipse = self.draw_point_coord(x, y, width, color)
            self.airport_items_dict[ellipse] = QtCore.QPointF(x, y)

        # Taxiway
        for taxiway in apt.taxiways:
            line_point_list = []
            path = QtGui.QPainterPath()
            pointF = self.scale_configuration.meters_to_scene(QtCore.QPointF(taxiway.coords[0].x, taxiway.coords[0].y))
            x, y = pointF.x(), pointF.y()
            path.moveTo(x, y)
            ellipse = self.draw_point_coord(x, y, width, color)
            line_point_list.append((ellipse, pointF))
            self.airport_items_dict[ellipse] = pointF

            for point in taxiway.coords[1:]:
                pointF = self.scale_configuration.meters_to_scene(QtCore.QPointF(point.x, point.y))
                x, y = pointF.x(), pointF.y()
                path.lineTo(x, y)
                ellipse = self.draw_point_coord(x, y, width, color)
                line_point_list.append((ellipse, pointF))
                self.airport_items_dict[ellipse] = pointF

            line = QtWidgets.QGraphicsPathItem(path)
            setHighlight(line, self)
            self.scene.addItem(line)
            self.airport_items_dict[line] = line_point_list

        # Runway
        for runway in apt.runways:
            line_point_list = []
            path = QtGui.QPainterPath()

            pointF_start = self.scale_configuration.meters_to_scene(QtCore.QPointF(runway.coords[0].x, runway.coords[0].y))
            pointF_end = self.scale_configuration.meters_to_scene(QtCore.QPointF(runway.coords[1].x, runway.coords[1].y))
            x_start, y_start = pointF_start.x(), pointF_start.y()
            x_end, y_end = pointF_end.x(), pointF_end.y()

            path.moveTo(x_start, y_start)
            ellipse_start = self.draw_point_coord(x_start, y_start, width, color)
            ellipse_end = self.draw_point_coord(x_end, y_end, width, color)
            path.lineTo(x_end, y_end)

            line_point_list.append((ellipse_start, pointF_start))
            line_point_list.append((ellipse_end, pointF_end))
            self.airport_items_dict[ellipse_start] = pointF_start
            self.airport_items_dict[ellipse_end] = pointF_end

            line = QtWidgets.QGraphicsPathItem(path)
            setHighlight(line, self)
            self.scene.addItem(line)
            self.airport_items_dict[line] = line_point_list


def highlight(item, widget):
    item.setPen(QtGui.QPen(item.pen().color(), item.pen().width() + 2))
    widget.on_item = True
    widget.current_item = item


def unhighlight(item, widget):
    item.setPen(QtGui.QPen(item.pen().color(), item.pen().width() - 2))
    widget.on_item = False
    widget.current_item = None


def setHighlight(item, widget):
    item.setAcceptHoverEvents(True)
    item.hoverEnterEvent = lambda event: highlight(item, widget)
    item.hoverLeaveEvent = lambda event: unhighlight(item, widget)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Scene = DrawAirport()
    sys.exit(app.exec_())

