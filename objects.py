from dataclasses import dataclass
from typing import List

@dataclass
class Point3D:
    x: float
    y: float
    z: float
    def __add__(self, other):
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)
    def __sub__(self, other):
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)
    def __mul__(self, scalar):
        return Point3D(self.x * scalar, self.y * scalar, self.z * scalar)
    def length(self):
        import math
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    def normalize(self):
        l = self.length()
        if l == 0: return Point3D(0,0,0)
        return Point3D(self.x/l, self.y/l, self.z/l)
    def dot(self, other):
        return self.x*other.x + self.y*other.y + self.z*other.z
    def cross(self, other):
        return Point3D(
            self.y*other.z - self.z*other.y,
            self.z*other.x - self.x*other.z,
            self.x*other.y - self.y*other.x
        )

@dataclass
class Object3D:
    name: str
    position: Point3D
    rotation: float
    obj_type: str
    id: int
    scale: float = 1.0
    selected: bool = False