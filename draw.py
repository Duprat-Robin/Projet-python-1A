from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import scene, airport, file_airport


POINT_Z_VALUE = 1
WAY_Z_VALUE = 0
AIRPORT_FILE = ""


class DrawAirport(scene.GraphicsWidget):
    def __init__(self):
        super().__init__()
        self.drawing_mode = 0  # 0: ne dessine pas 1: dessine des points 2: dessine des lignes 3: efface des points
        self.line_point_list = []
        self.on_item = False # pas encore utilisé...

    def mousePressEvent(self, event):
        if (self.scale_configuration.scale_point == 0 or self.scale_configuration.scale_point == 1) and self.scale_configuration.scale_set:
            self.scale_configuration.setScale()
        if self.drawing_mode == 1 or self.drawing_mode == 2:
            self.draw_point()
        elif self.drawing_mode == 3:
            self.delete_point() 
        self.view.update()

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self.drawing_mode == 2 and len(self.line_point_list) != 0:
            self.draw_line()
            self.line_point_list = []
        self.view.update()

    def drawing_mode_reset(self):
        self.drawing_mode = 0

    def drawing_mode_point(self):
        self.drawing_mode = 1

    def drawing_mode_line(self):
        self.drawing_mode = 2

    def deleting_mode_point(self):
        self.drawing_mode = 3

    def draw_point(self):
        width = 20
        color = QtGui.QColor(255, 0, 0)
        #pen = QtGui.QPen(color)
        pos_cursor_scene = self.get_coordonates_scene()
        coor_point = QtCore.QRectF(pos_cursor_scene.x() - width / 2, pos_cursor_scene.y() - width / 2, width, width)
        point = QtWidgets.QGraphicsEllipseItem(coor_point)
        point.setBrush(QtGui.QBrush(color))
        setHighlight(point)
        self.scene.addItem(point)
        #point.setPen(pen)
        if self.drawing_mode == 2:
            self.line_point_list.append(pos_cursor_scene)

    def draw_line(self):
        width = 10
        color = QtGui.QColor(0, 255, 0)
        # pen = QtGui.QPen(color)
        # pen.setWidth(width)
        path = QtGui.QPainterPath()
        path.moveTo(self.line_point_list[0].x(), self.line_point_list[0].y())
        for point in self.line_point_list[1:]:
            path.lineTo(point.x(), point.y())
        line = QtWidgets.QGraphicsPathItem(path)
        setHighlight(line)
        self.scene.addItem(line)
        
        # line.setPen(pen)

    # def delete_point(self): 
    #     pos_cursor_scene = self.get_coordonates_scene()
    #     self.view.update()  # met à jour la vue

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

def highlight(item):
    item.setPen(QtGui.QPen(item.pen().color(), item.pen().width() + 2))
    
def unhighlight(item):
    item.setPen(QtGui.QPen(item.pen().color(), item.pen().width() - 2))
    
def setHighlight(item):
    item.setAcceptHoverEvents(True)
    item.hoverEnterEvent = lambda event: highlight(item)
    item.hoverLeaveEvent = lambda event: unhighlight(item)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Scene = DrawAirport()
    sys.exit(app.exec_())
