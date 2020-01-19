from PyQt5 import QtWidgets, QtGui, QtCore
import enum
import scene, geometry


class Mode(enum.Enum):
    """0: default mode (draw disable) 1: draw points 2: draw lines 3: erase items"""
    DEFAULT = 0
    DRAW_POINT = 1
    DRAW_LINE = 2
    DELETE = 3


class LineType(enum.Enum):
    UNDEFINED = None
    TAXIWAY = 'T'
    RUNWAY = 'R'


class InspectorSignal(QtCore.QObject):
    ask_inspection_signal = QtCore.pyqtSignal()


class PointItem():
    def __init__(self, coordinates, saved=False):
        self.coordinates = coordinates
        self.saved = saved
        self.point = None  # None | NamedPoint

    def update_coordinates(self, new_coord, meter_coord):
        """new_coord is a QPoint"""
        self.coordinates = new_coord
        if self.saved:
            self.point.x, self.point.y = int(meter_coord.x()), int(meter_coord.y())


class LineItem():
    def __init__(self, list_coordinates, saved=False):
        self.list_coordinates = list_coordinates
        self.saved = saved
        self.line = None  # None | Taxiway or Runway
        self.type = LineType.UNDEFINED

    def update_list_coordinates(self, new_point_coord, meters_coord_point, item, position):
        self.list_coordinates[position] = (item, new_point_coord)
        if self.saved:
            point = geometry.Point(int(meters_coord_point.x()), int(meters_coord_point.y()))
            if self.type == LineType.TAXIWAY:
                self.line.coords[position] = point
            elif self.type == LineType.RUNWAY:
                self.line.ends[position] = point

    def del_point(self, i):
        if self.saved:
            self.line.coords.pop(i)


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
        self.last_drawn_point = None
        self.point_to_line_dict = {}

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton and self.cursor_mode == Mode.DEFAULT and not(self.highlighted_item is None) and (self.current_item is None or not(type(self.current_item) is QtWidgets.QGraphicsEllipseItem)) and not(type(self.highlighted_item) is QtWidgets.QGraphicsPathItem):
            removed_item = self.highlighted_item
            temporary_point = self.airport_items_dict.pop(removed_item)  # PointItem or LineItem
            self.scene.removeItem(removed_item)
            self.draw_point()
            new_coord = self.get_coordinates_scene()
            meters_coord = self.scale_configuration.scene_to_meters(new_coord)
            temporary_point.update_coordinates(new_coord, meters_coord)
            last_key_value = self.airport_items_dict.popitem()
            self.airport_items_dict[last_key_value[0]] = temporary_point
            self.current_item, self.clicked_item, self.highlighted_item = self.last_drawn_point, self.last_drawn_point, self.last_drawn_point
            self.on_item = True
            highlight(self.highlighted_item, self)
            if removed_item in self.point_to_line_dict:
                list_line_tuple = self.point_to_line_dict[removed_item]  # (line, point's pos in line)
                self.point_to_line_dict.pop(removed_item)
                new_point_coord = self.airport_items_dict[self.last_drawn_point].coordinates
                meters_point_coord = self.scale_configuration.scene_to_meters(new_point_coord)
                for line_tuple in list_line_tuple:
                    line, i = line_tuple[0], line_tuple[1]
                    self.line_point_list = self.airport_items_dict[line].list_coordinates
                    for point in [self.line_point_list[j] for j in range(len(self.line_point_list)) if j != i]:
                        length = len(self.point_to_line_dict[point[0]])
                        j = 0
                        while j < length:
                            if self.point_to_line_dict[point[0]][j][0] == line:
                                self.point_to_line_dict[point[0]].pop(j)
                                length -= 1
                            else:
                                j += 1
                    self.line_point_list[i] = (self.last_drawn_point, new_point_coord)
                    temporary_line = self.airport_items_dict.pop(line)
                    self.scene.removeItem(line)
                    self.draw_line()
                    temporary_line.update_list_coordinates(new_point_coord, meters_point_coord, self.last_drawn_point, i)
                    last_key_value = self.airport_items_dict.popitem()
                    self.airport_items_dict[last_key_value[0]] = temporary_line
                    self.line_point_list = []
        if self.cursor_mode == Mode.DRAW_POINT or self.cursor_mode == Mode.DRAW_LINE:
            self.draw_point()
            if self.highlighted_item is not None:
                unhighlight(self.highlighted_item, self)
            self.highlighted_item = self.last_drawn_point
            highlight(self.highlighted_item, self)
            self.signal.ask_inspection_signal.emit()
        if self.cursor_mode == Mode.DELETE:
            self.delete()
        if self.cursor_mode == Mode.DEFAULT and event.button() == QtCore.Qt.LeftButton:
            if self.on_item:
                self.clicked_item = self.current_item
                if self.highlighted_item is not None and self.clicked_item is not self.highlighted_item:
                    unhighlight(self.highlighted_item, self)
                    self.highlighted_item = None
                if self.clicked_item != self.highlighted_item:
                    highlight(self.clicked_item, self)
                    self.highlighted_item = self.clicked_item
                self.signal.ask_inspection_signal.emit()
            elif self.highlighted_item is not None:
                unhighlight(self.highlighted_item, self)
                self.highlighted_item = None
                self.clicked_item = None
                self.signal.ask_inspection_signal.emit()
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
        ellipse.setZValue(1)
        return ellipse

    def draw_point(self):
        if self.current_item is None or not (type(self.current_item) is QtWidgets.QGraphicsEllipseItem):
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
            point.setZValue(1)
            self.airport_items_dict[point] = PointItem(pos_cursor_scene)
            self.last_drawn_point = point
            if self.cursor_mode == Mode.DRAW_LINE:
                self.line_point_list.append((point, pos_cursor_scene))
        elif self.cursor_mode == Mode.DRAW_LINE:
            self.line_point_list.append((self.current_item, self.airport_items_dict[self.current_item].coordinates))
        # print("test", pos_cursor_scene, self.scale_configuration.meters_to_scene(self.scale_configuration.scene_to_meters(pos_cursor_scene)))

    def draw_line(self):
        path = QtGui.QPainterPath()
        path.moveTo(self.line_point_list[0][1].x(), self.line_point_list[0][1].y())
        for point in self.line_point_list[1:]:
            path.lineTo(point[1].x(), point[1].y())
        line = QtWidgets.QGraphicsPathItem(path)
        line.setZValue(0)
        setHighlight(line, self)
        self.scene.addItem(line)
        self.airport_items_dict[line] = LineItem(self.line_point_list)
        i = 0
        for point in self.line_point_list:
            if point[0] in self.point_to_line_dict:
                self.point_to_line_dict[point[0]].append((line, i))
            else:
                self.point_to_line_dict[point[0]] = [(line, i)]
            i += 1

    def delete(self):
        if not(self.current_item is None):
            if self.current_item in self.point_to_line_dict:
                list_line = self.point_to_line_dict[self.current_item]
                self.point_to_line_dict.pop(self.current_item)
                for line_tuple in list_line:
                    line, i = line_tuple[0], line_tuple[1]
                    self.line_point_list = self.airport_items_dict[line].list_coordinates
                    length_list = len(self.line_point_list)
                    if length_list >= 3:
                        for point in [self.line_point_list[j] for j in range(len(self.line_point_list)) if j != i]:
                            length = len(self.point_to_line_dict[point[0]])
                            j = 0
                            while j < length:
                                if self.point_to_line_dict[point[0]][j][0] == line:
                                    self.point_to_line_dict[point[0]].pop(j)
                                    length -= 1
                                else:
                                     j += 1
                        self.line_point_list.pop(i)
                        self.scene.removeItem(line)
                        temporary_line = self.airport_items_dict.pop(line)
                        self.draw_line()
                        temporary_line.del_point(i)
                        last_key_value = self.airport_items_dict.popitem()
                        self.airport_items_dict[last_key_value[0]] = temporary_line

                    elif length_list == 2:
                        self.scene.removeItem(line)
                        pos = 1 - i
                        other_point = self.line_point_list[pos][0]
                        length = len(self.point_to_line_dict[other_point])
                        if length > 1:
                            j = 0
                            while j < length:
                                if self.point_to_line_dict[other_point][j][0] == line:
                                    self.point_to_line_dict[other_point].pop(j)
                                    length -= 1
                                else:
                                    j += 1
                        else:
                            self.point_to_line_dict.pop(other_point)
                            self.scene.removeItem(other_point)
                        item = self.airport_items_dict.pop(line)
                        if item.saved:
                            self.del_twy_rwy(item)
                    self.line_point_list = []

            elif type(self.current_item) is QtWidgets.QGraphicsPathItem:
                for point in self.airport_items_dict[self.current_item].list_coordinates:
                    length = len(self.point_to_line_dict[point[0]])
                    if length > 1:
                        j = 0
                        while j < length:
                            if self.point_to_line_dict[point[0]][j][0] == self.current_item:
                                self.point_to_line_dict[point[0]].pop(j)
                                length -= 1
                            else:
                                j += 1
                    else:
                        self.point_to_line_dict.pop(point[0])
                item = self.airport_items_dict[self.current_item]
                self.del_twy_rwy(item)
            else:
                item = self.airport_items_dict[self.current_item]
                if item.saved:
                    index = self.airport_file.airport.points.index(item.point)
                    self.airport_file.airport.points.pop(index)
                    self.airport_file.airport.pt_dict.pop(item.point.name)
            self.scene.removeItem(self.current_item)
            self.airport_items_dict.pop(self.current_item)
        self.on_item = False
        self.current_item = None

    def del_twy_rwy(self, item):
        if item.saved:
            if item.type == LineType.TAXIWAY:
                index = self.airport_file.airport.taxiways.index(item.line)
                self.airport_file.airport.taxiways.pop(index)
            elif item.type == LineType.RUNWAY:
                index = self.airport_file.airport.runways.index(item.line)
                self.airport_file.airport.runways.pop(index)
                self.airport_file.airport.qfu_dict.pop(item.line.qfus[0])
                self.airport_file.airport.qfu_dict.pop(item.line.qfus[1])

    def draw_airport_points(self):
        self.airport_file.airport.display_name()
        apt = self.airport_file.airport
        width = 20
        color = QtGui.QColor(255, 0, 0)

        # NamedPoint
        for point in apt.points:
            pointF = self.scale_configuration.meters_to_scene(QtCore.QPointF(point.x, point.y))
            x, y = pointF.x(), pointF.y()
            ellipse = self.draw_point_coord(x, y, width, color)
            self.airport_items_dict[ellipse] = PointItem(QtCore.QPointF(x, y), True)
            self.airport_items_dict[ellipse].point = point

        # Taxiway
        for taxiway in apt.taxiways:
            line_point_list = []
            path = QtGui.QPainterPath()
            pointF = self.scale_configuration.meters_to_scene(QtCore.QPointF(taxiway.coords[0].x, taxiway.coords[0].y))
            x, y = pointF.x(), pointF.y()
            path.moveTo(x, y)
            ellipse = self.draw_point_coord(x, y, width, color)
            line_point_list.append((ellipse, pointF))
            self.airport_items_dict[ellipse] = PointItem(pointF)

            for point in taxiway.coords[1:]:
                pointF = self.scale_configuration.meters_to_scene(QtCore.QPointF(point.x, point.y))
                x, y = pointF.x(), pointF.y()
                path.lineTo(x, y)
                ellipse = self.draw_point_coord(x, y, width, color)
                line_point_list.append((ellipse, pointF))
                self.airport_items_dict[ellipse] = PointItem(pointF)
            line = QtWidgets.QGraphicsPathItem(path)
            setHighlight(line, self)
            self.scene.addItem(line)
            line.setZValue(0)
            i = 0
            for point in line_point_list:
                if point[0] in self.point_to_line_dict:
                    self.point_to_line_dict[point[0]].append((line, i))
                else:
                    self.point_to_line_dict[point[0]] = [(line, i)]
                i += 1
            self.airport_items_dict[line] = LineItem(line_point_list, True)
            self.airport_items_dict[line].line = taxiway
            self.airport_items_dict[line].type = LineType.TAXIWAY

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
            self.airport_items_dict[ellipse_start] = PointItem(pointF_start)
            self.airport_items_dict[ellipse_end] = PointItem(pointF_end)
            line = QtWidgets.QGraphicsPathItem(path)
            setHighlight(line, self)
            line.setZValue(0)
            
            self.scene.addItem(line)
            if ellipse_start in self.point_to_line_dict :
                self.point_to_line_dict[ellipse_start].append((line,0))
            else :
                self.point_to_line_dict[ellipse_start] = [(line,0)]
            if ellipse_end in self.point_to_line_dict :
                 self.point_to_line_dict[ellipse_end].append((line,1))
            else :
                self.point_to_line_dict[ellipse_end] = [(line,1)]
            self.airport_items_dict[line] = LineItem(line_point_list, True)
            self.airport_items_dict[line].line = runway
            self.airport_items_dict[line].type = LineType.RUNWAY


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

