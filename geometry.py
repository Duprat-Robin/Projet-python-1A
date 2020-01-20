class Point(object):
    """units are in meters for x and y"""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "({0.x}, {0.y})".format(self)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __rmul__(self, k):
        return Point(k * self.x, k * self.y)

    def __abs__(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def sca(self, other):
        """scalar product between self and other"""
        return self.x * other.x + self.y * other.y

    def det(self, other):
        """det(Point) return float
        returns the determinant between self and other"""
        return self.x * other.y - self.y * other.x

    def distance(self, other):
        return abs(self - other)

    def seg_dist(self, a, b):
        ab, ap, bp = b - a, self - a, self - b
        if ab.sca(ap) <= 0:
            return abs(ap)
        elif ab.sca(bp) >= 0:
            return abs(bp)
        else:
            return abs(ab.det(ap)) / abs(ap)


class PolyLine(object):
    def __init__(self, coords):
        self.length = sum(pi.distance(coords[i - 1])
                          for i, pi in enumerate(coords[1:]))
        self.coords = coords

    def __repr__(self):
        return "<geometry.Line {}>".format(len(self))

    def __str__(self):
        points = ', '.join(str(p) for p in self.coords)
        return 'PolyLine {}m: ({})'.format(self.length, points)

    def __len__(self):
        return len(self.coords)
