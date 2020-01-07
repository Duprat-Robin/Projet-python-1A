"""Rewrite openFile and saveFile to apply file's structure of py-airport
openFile will use a function/method from airport to load the project
or airport can use openFile if we want to avoid cross importation
draw import file_airport and airport, file_airport import airport (airport doesn't import file_airport)"""

from PyQt5 import QtWidgets
import os
import airport, geometry

categories = {'L': airport.WakeVortexCategory.LIGHT,
              'M': airport.WakeVortexCategory.MEDIUM,
              'H': airport.WakeVortexCategory.HEAVY}
point_types = [airport.PointType.STAND, airport.PointType.DEICING, airport.PointType.RUNWAY_POINT]


class FileAirport():
    def __init__(self):
        self.name = ""
        self.airport = None  # airport.Airport()

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
        repository = QtWidgets.QFileDialog()
        self.name = repository.getOpenFileName()
        points, taxiways, runways = {}, {}, {}
        path = self.name[0]
        file = open(path, 'r')
        airport_name = file.readline().split()[0]
        lines = file.readlines()
        for line in lines:
            words = line.strip().split()
            name = words[1]
            try:
                if words[0] == 'P':  # Point description
                    pt_type = point_types[int(words[2])]
                    points[name] = airport.NamedPoint(name, pt_type, words[3])
                elif words[0] == 'L':  # Taxiway description
                    speed = int(words[2])
                    cat = categories[words[3]]
                    one_way = words[4] == 'S'
                    xys = xys_to_points(words[5:])
                    taxiways[name] = airport.Taxiway(name, speed, cat, one_way, xys)
                elif words[0] == 'R':  # Runway description
                    pts = tuple(words[4].split(','))
                    xys = xys_to_points(words[5:])
                    runways[name] = airport.Runway(name, words[2], words[3], xys, pts)
            except Exception as error:
                print(error, line)
            file.close()
        self.airport = airport.Airport(airport_name, points, taxiways, runways)

    def saveFile(self):
        """Save the file with its current name in its current location"""
        path = self.name[0]
        with open(path, 'w') as file:
            lines = [self.airport.name + "\n"]
            points = self.airport.points
            taxiways = self.airport.taxiways
            runways = self.airport.runways
            for name in points:
                point = points[name]
                if point.type == point_types[0]:
                    type = 0
                elif point.type == point_types[1]:
                    type = 1
                elif point.type == point_types[2]:
                    type = 2
                lines.append("P {0.name} {1} {0.x},{0.y}\n".format(point, type))
            for name in taxiways:
                taxiway = taxiways[name]
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
                coords_str = tuple_to_str(taxiway.coords)
                lines.append("L {0.name} {0.speed} {1} {2}".format(taxiway, cat, one_way))
                lines[-1] = " ".join([lines[-1], coords_str, "\n"])
            for name in runways:
                runway = runways[name]
                points_str = tuple_to_str(runway.named_points)
                ends_str = tuple_to_str(runway.coords)
                lines.append("R {0.name} {0.qfus[0]} {0.qfus[1]} ".format(runway))
                lines[-1] = " ".join([lines[-1], points_str, ends_str, "\n"])
            file.writelines(lines)

    def saveAsFile(self):
        """Save the file with the name chosen by the user in the folder chose in the file explorer of the computer"""
        if self.name[0][:8] == "untitled":
            os.remove(self.name[0])
        repository = QtWidgets.QFileDialog()
        self.name = repository.getOpenFileName()
        self.saveFile()


def tuple_to_str(coords):
    return " ".join((str(i).strip('()') for i in coords))


def xys_to_points(str_xy_list):
    """ xys_to_points(str list) returns Point tuple: converts x,y str list to Point tuple"""

    def xy_to_point(str_xy):
        x, y = map(int, str_xy.split(','))
        return geometry.Point(x, y)

    return tuple(xy_to_point(str_xy) for str_xy in str_xy_list)


if __name__ == "__main__":
    airport_f = FileAirport()
    airport_f.openFile("lfpg_map.txt")
    airport_f.saveAsFile("new_lfbg_map.txt")
