"""Rewrite openFile and saveFile to apply file's structure of py-airport
openFile will use a function/method from airport to load the project
or airport can use openFile if we want to avoid cross importation
draw import file_airport and airport, file_airport import airport (airport doesn't import file_airport)"""


from PyQt5 import QtWidgets, QtCore
import os
import airport, geometry

categories = {'L': airport.WakeVortexCategory.LIGHT,
              'M': airport.WakeVortexCategory.MEDIUM,
              'H': airport.WakeVortexCategory.HEAVY}
point_types = [airport.PointType.STAND, airport.PointType.DEICING, airport.PointType.RUNWAY_POINT]


class ImageSignal(QtCore.QObject):
    ask_image_signal = QtCore.pyqtSignal(str)


class FileAirport():

    def __init__(self):
        self.name = ""
        self.airport = airport.Airport()
        self.image_signal = ImageSignal()
        self.image_repository = ""

    def newFile(self):
        """Thanks to naming, we can create an infinity of files without Saving then under an other name
        But, the default repository is the folder of the software"""
        def naming():
            c = 0
            while os.path.isfile("untitled{}.txt".format(c)):
                c += 1
            return c
        c = naming()
        self.name = ("untitled{}.txt".format(c), True)  # What's this Boolean?
        with open(self.name[0], 'w') as file:
            pass

    def openFile(self):
        """Open the file selected in the file explorer of the computer"""
        try:
            repository = QtWidgets.QFileDialog()
            self.name = repository.getOpenFileName()
            points, taxiways, runways = [], [], []
            origin = QtCore.QPointF(0, 0)
            factor = (1, 1, 1)

            path = self.name[0]
            file = open(path, 'r')
            airport_name = file.readline().split()[0]
            lines = file.readlines()
            for line in lines:
                words = line.strip().split()
                name = words[1]
                try:
                    if words[0] == 'I':  # Image description
                        self.image_repository = words[1]
                        self.image_signal.ask_image_signal.emit(self.image_repository)
                    if words[0] == 'O':  # Origin and scale factor description
                        xy_str = words[1].split(',')
                        x, y = float(xy_str[0]), float(xy_str[1])
                        origin = QtCore.QPointF(x, y)
                        factor = (float(words[2]), float(words[3]), float(words[4]))
                    if words[0] == 'P':  # Point description
                        pt_type = point_types[int(words[2])]
                        points.append(airport.NamedPoint(name, pt_type, words[3]))
                    elif words[0] == 'L':  # Taxiway description
                        speed = int(words[2])
                        cat = categories[words[3]]
                        one_way = words[4] == 'S'
                        xys = xys_to_points(words[5:])
                        taxiways.append(airport.Taxiway(name, speed, cat, one_way, xys))
                    elif words[0] == 'R':  # Runway description
                        pts = tuple(words[4].split(','))
                        xys = xys_to_points(words[5:])
                        runways.append(airport.Runway(name, words[2], words[3], xys, pts))
                except Exception as error:
                    print(error, line)
                file.close()
            self.airport = airport.Airport(airport_name, points, taxiways, runways, origin, factor)
        except Exception:
            pass

    def saveFile(self):
        """Save the file with its current name in its current location"""
        path = self.name[0]
        lines = []
        with open(path, 'w') as file:
            lines.append(self.airport.name + "\n")
            lines.append("I {0}\n".format(self.image_repository))
            lines.append("O {0},{1} {2[0]} {2[1]} {2[2]}\n".format(self.airport.origin.x(), self.airport.origin.y(),
                                                                   self.airport.factor))
            points = self.airport.points
            taxiways = self.airport.taxiways
            runways = self.airport.runways
            for point in points:
                if point.type == point_types[0]:
                    type = 0
                elif point.type == point_types[1]:
                    type = 1
                elif point.type == point_types[2]:
                    type = 2
                lines.append("P {0.name} {1} {0.x},{0.y}\n".format(point, type))
            for taxiway in taxiways:
                if taxiway.cat == categories['L']:
                    cat = 'L'
                elif taxiway.cat == categories['M']:
                    cat = 'M'
                elif taxiway.cat == categories['H']:
                    cat = 'H'
                if taxiway.one_way:
                    one_way = 'S'
                else:
                    one_way = 'D'
                coords_str = tuple_to_str([(i.x, i.y) for i in taxiway.coords])
                lines.append("L {0.name} {0.speed} {1} {2}".format(taxiway, cat, one_way))
                lines[-1] = " ".join([lines[-1], coords_str, "\n"])
            for runway in runways:
                ends_str = tuple_to_str([(i.x, i.y) for i in runway.coords])
                lines.append("R {0.name} {0.qfus[0]} {0.qfus[1]} ".format(runway))
                lines[-1] = " ".join([lines[-1], ",".join(runway.named_points), ends_str, "\n"])
            file.writelines(lines)

    def saveAsFile(self):
        """Save the file with the name chosen by the user in the folder chose in the file explorer of the computer"""
        try:
            if self.name[0][:8] == "untitled":
                os.remove(self.name[0])
        except Exception:
            pass

        try:
            repository = QtWidgets.QFileDialog()
            self.name = repository.getSaveFileName()
            self.saveFile()
        except Exception as error:
            print(error)


def tuple_to_str(coords):
    return " ".join(("{0[0]},{0[1]}".format(i) for i in coords))


def xys_to_points(str_xy_list):
    """ xys_to_points(str list) returns Point tuple: converts x,y str list to Point tuple"""

    def xy_to_point(str_xy):
        x, y = map(int, str_xy.split(','))
        return geometry.Point(x, y)

    return list(xy_to_point(str_xy) for str_xy in str_xy_list)
