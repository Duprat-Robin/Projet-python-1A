from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import scene, airport, file_airport


POINT_Z_VALUE = 1
WAY_Z_VALUE = 0
AIRPORT_FILE = ""


class DrawAirport(scene.GraphicsScene):
    def __init__(self):
        super().__init__()
        self.point_group = QtWidgets.QGraphicsItemGroup()
        self.scene.addItem(self.point_group)
        self.point_group.setZValue(POINT_Z_VALUE)

    def mousePressEvent(self, event):
        print("mouse press")
        self.draw_point()
        if (self.scale_configuration.scale_point == 0 or self.scale_configuration.scale_point == 1) and self.scale_configuration.scale_set:
            self.scale_configuration.setScale()
        self.view.update()

    def draw_point(self):
        width = 100
        #factor = self.size().height()*RATIO / old_height_screen
        factor = 1
        color = QtGui.QColor(255, 0, 0)
        pen = QtGui.QPen(color)
        pos_cursor = self.cursor().pos()
        coor_point = QtCore.QRectF(pos_cursor.x()*factor, pos_cursor.y()*factor, width, width)
        point = QtWidgets.QGraphicsEllipseItem(coor_point, self.point_group)
        point.setPen(pen)

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


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Scene = DrawAirport()
    sys.exit(app.exec_())
