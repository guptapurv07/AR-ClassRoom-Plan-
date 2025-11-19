import math
from objects import Point3D

class Camera:
    def __init__(self):
        self.distance = 700
        self.angle_h = 45
        self.angle_v = 35
        self.target = Point3D(0, 0, 0)
        self.fov = 60

    def get_position(self):
        rad_h = math.radians(self.angle_h)
        rad_v = math.radians(self.angle_v)
        x = self.target.x + self.distance * math.cos(rad_v) * math.cos(rad_h)
        y = self.target.y + self.distance * math.sin(rad_v)
        z = self.target.z + self.distance * math.cos(rad_v) * math.sin(rad_h)
        return Point3D(x, y, z)

    def get_basis(self):
        cam_pos = self.get_position()
        f = Point3D(self.target.x - cam_pos.x, self.target.y - cam_pos.y, self.target.z - cam_pos.z)
        fl = math.sqrt(f.x**2 + f.y**2 + f.z**2)
        f = Point3D(f.x / fl, f.y / fl, f.z / fl)
        up_world = Point3D(0, 1, 0)
        rx = f.y * up_world.z - f.z * up_world.y
        ry = f.z * up_world.x - f.x * up_world.z
        rz = f.x * up_world.y - f.y * up_world.x
        rl = math.sqrt(rx**2 + ry**2 + rz**2) or 1.0
        right = Point3D(rx / rl, ry / rl, rz / rl)
        ux = right.y * f.z - right.z * f.y
        uy = right.z * f.x - right.x * f.z
        uz = right.x * f.y - right.y * f.x
        up = Point3D(ux, uy, uz)
        return right, up, f, cam_pos

    def project(self, point: Point3D, screen_width: int, screen_height: int):
        right, up, fwd, cam_pos = self.get_basis()
        px = point.x - cam_pos.x
        py = point.y - cam_pos.y
        pz = point.z - cam_pos.z
        x_cam = px * right.x + py * right.y + pz * right.z
        y_cam = px * up.x + py * up.y + pz * up.z
        z_cam = px * fwd.x + py * fwd.y + pz * fwd.z
        if z_cam <= 1e-3:
            return (screen_width // 2, screen_height // 2)
        aspect = screen_width / max(1, screen_height)
        tan_half = math.tan(math.radians(self.fov) / 2)
        nx = (x_cam / (z_cam * tan_half)) / aspect
        ny = (y_cam / (z_cam * tan_half))
        sx = int((nx * 0.5 + 0.5) * screen_width)
        sy = int((1.0 - (ny * 0.5 + 0.5)) * screen_height)
        return (sx, sy)

    def screen_to_ray(self, sx: int, sy: int, screen_width: int, screen_height: int):
        right, up, fwd, cam_pos = self.get_basis()
        x_ndc = (sx / max(1, screen_width)) * 2 - 1
        y_ndc = 1 - (sy / max(1, screen_height)) * 2
        aspect = screen_width / max(1, screen_height)
        tan_half = math.tan(math.radians(self.fov) / 2)
        dx = x_ndc * aspect * tan_half
        dy = y_ndc * tan_half
        dir_x = dx * right.x + dy * up.x + fwd.x
        dir_y = dx * right.y + dy * up.y + fwd.y
        dir_z = dx * right.z + dy * up.z + fwd.z
        dl = math.sqrt(dir_x**2 + dir_y**2 + dir_z**2) or 1.0
        return cam_pos, Point3D(dir_x / dl, dir_y / dl, dir_z / dl)

    def unproject(self, screen_x: int, screen_y: int, screen_width: int, screen_height: int, y: float = 0.0):
        origin, direction = self.screen_to_ray(screen_x, screen_y, screen_width, screen_height)
        if abs(direction.y) < 1e-5:
            return Point3D(origin.x, y, origin.z)
        t = (y - origin.y) / direction.y
        if t <= 0:
            return Point3D(origin.x + direction.x * 1.0, y, origin.z + direction.z * 1.0)
        hit = Point3D(origin.x + direction.x * t, y, origin.z + direction.z * t)
        return hit