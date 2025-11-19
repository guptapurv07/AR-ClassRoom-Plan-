import pygame
import math
import json
import os
import cv2  # Added for OpenCV operations
import cv2.aruco as aruco  # Added for AruCo detection/generation
import numpy as np  # Added for array handling with OpenCV
import threading
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from camera import Camera
from objects import Point3D, Object3D
from ui import UI
from ar_camera import ARCamera # Assumes ar_camera.py is created and available

@dataclass
class AdvancedClassroomPlanner:
    def __init__(self):
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        os.environ.setdefault("SDL_VIDEO_ALLOW_SCREENSAVER", "1")
        os.environ.setdefault("SDL_VIDEO_HIGHDPI", "1")
        pygame.init()

        self.WINDOW_WIDTH = 1600
        self.WINDOW_HEIGHT = 900
        self.FPS = 60
        self.GRID_SIZE = 25
        self.UNITS_PER_FOOT = 25

        flags = pygame.RESIZABLE | pygame.SCALED | pygame.DOUBLEBUF
        try:
            self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), flags, vsync=1)
        except TypeError:
            self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), flags)
        pygame.display.set_caption("Advanced AR Classroom Planner • Python 3D")

        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        icon.fill((0, 0, 0, 0))
        pygame.draw.rect(icon, (30, 58, 138), pygame.Rect(0, 0, 32, 32), border_radius=6)
        pygame.draw.rect(icon, (59, 130, 246), pygame.Rect(2, 2, 28, 28), 2, border_radius=6)
        fnt = pygame.font.SysFont("Segoe UI", 16, bold=True)
        txt = fnt.render("AR", True, (255, 255, 255))
        icon.blit(txt, txt.get_rect(center=(16, 17)))
        pygame.display.set_icon(icon)

        self.clock = pygame.time.Clock()
        self.running = True
        self.window_width = self.WINDOW_WIDTH
        self.window_height = self.WINDOW_HEIGHT
        self.ui_scale = min(self.window_width / 1600, self.window_height / 900)

        self.app_state = "SETUP"
        self.door_angle = 0
        self.grid_width = 0
        self.grid_depth = 0
        self.grid_height = 0

        self.width_input_str = ""
        self.depth_input_str = ""
        self.height_input_str = ""
        self.active_input = "WIDTH"
        self.setup_error_msg = ""

        self.camera = Camera()
        self.objects: List[Object3D] = []
        self.selected_object_type = "chair"
        self.selected_object: Optional[Object3D] = None
        self.next_id = 1

        self.dragging_camera = False
        self.dragging_object = False
        self.rotating_object = False
        self.last_mouse_pos = (0, 0)
        self.mouse_world_pos = Point3D(0, 0, 0)
        self.right_click_start = None
        self.active_button: Optional[str] = None

        self.history: List[List[Object3D]] = []
        self.history_index = -1
        self.max_history = 50

        self.snap_to_grid = True
        self.show_grid = True
        self.show_help = False
        self.MIN_W, self.MIN_H = 1024, 640

        pygame.font.init()
        self.ui = UI(self)
        
        # --- AR CAMERA AND DETECTOR SETUP ---
        self.ar_camera = ARCamera()
        self.ar_mode_active = False
        
        print("Initializing AruCo detector...")
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
        self.aruco_parameters = aruco.DetectorParameters()
        self.aruco_detector = aruco.ArucoDetector(self.aruco_dict, self.aruco_parameters)
        self.next_marker_id = 23  # Starting ID for marker generation
        print("Detector initialized.")
        # ------------------------------------
        
        self.vignette_surface = self.create_vignette()
        self.setup_ui_elements()
        self.ui.setup_ui()

    def create_vignette(self):
        vignette_surface = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        edge_size = 150
        for i in range(edge_size):
            alpha = int((i / edge_size) * 80)
            pygame.draw.line(vignette_surface, (0, 0, 0, alpha), (0, i), (self.window_width, i))
            pygame.draw.line(vignette_surface, (0, 0, 0, alpha), (0, self.window_height - 1 - i), (self.window_width, self.window_height - 1 - i))
            pygame.draw.line(vignette_surface, (0, 0, 0, alpha), (i, 0), (i, self.window_height))
            pygame.draw.line(vignette_surface, (0, 0, 0, alpha), (self.window_width - 1 - i, 0), (self.window_width - 1 - i, self.window_height))
        return vignette_surface

    def setup_ui_elements(self):
        center_x = self.window_width // 2
        center_y = self.window_height // 2
        input_w, input_h = 400, 50
        self.width_input_rect = pygame.Rect(center_x - input_w // 2, center_y - 160, input_w, input_h)
        self.depth_input_rect = pygame.Rect(center_x - input_w // 2, center_y - 50, input_w, input_h)
        self.height_input_rect = pygame.Rect(center_x - input_w // 2, center_y + 60, input_w, input_h)
        self.start_button_rect = pygame.Rect(center_x - input_w // 2, center_y + 160, input_w, 50)

    def save_state(self):
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        state = [Object3D(
            name=obj.name,
            position=Point3D(obj.position.x, obj.position.y, obj.position.z),
            rotation=obj.rotation,
            obj_type=obj.obj_type,
            id=obj.id,
            scale=obj.scale
        ) for obj in self.objects]
        self.history.append(state)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.history_index += 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.objects = [Object3D(
                name=obj.name,
                position=Point3D(obj.position.x, obj.position.y, obj.position.z),
                rotation=obj.rotation,
                obj_type=obj.obj_type,
                id=obj.id,
                scale=obj.scale
            ) for obj in self.history[self.history_index]]

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.objects = [Object3D(
                name=obj.name,
                position=Point3D(obj.position.x, obj.position.y, obj.position.z),
                rotation=obj.rotation,
                obj_type=obj.obj_type,
                id=obj.id,
                scale=obj.scale
            ) for obj in self.history[self.history_index]]

    def handle_setup_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.width_input_rect.collidepoint(event.pos):
                        self.active_input = "WIDTH"
                    elif self.depth_input_rect.collidepoint(event.pos):
                        self.active_input = "DEPTH"
                    elif self.height_input_rect.collidepoint(event.pos):
                        self.active_input = "HEIGHT"
                    elif self.start_button_rect.collidepoint(event.pos):
                        self.active_button = "START"
                    else:
                        self.active_input = None
                    self.setup_error_msg = ""
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.active_button == "START" and self.start_button_rect.collidepoint(event.pos):
                        self.validate_and_start()
                    self.active_button = None
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    self.validate_and_start()
                elif event.key == pygame.K_TAB:
                    if self.active_input == "WIDTH": self.active_input = "DEPTH"
                    elif self.active_input == "DEPTH": self.active_input = "HEIGHT"
                    else: self.active_input = "WIDTH"
                elif event.key == pygame.K_BACKSPACE:
                    if self.active_input == "WIDTH": self.width_input_str = self.width_input_str[:-1]
                    elif self.active_input == "DEPTH": self.depth_input_str = self.depth_input_str[:-1]
                    elif self.active_input == "HEIGHT": self.height_input_str = self.height_input_str[:-1]
                else:
                    if event.unicode.isdigit() or event.unicode == '.':
                        if self.active_input == "WIDTH" and len(self.width_input_str) < 10:
                            self.width_input_str += event.unicode
                        elif self.active_input == "DEPTH" and len(self.depth_input_str) < 10:
                            self.depth_input_str += event.unicode
                        elif self.active_input == "HEIGHT" and len(self.height_input_str) < 10:
                            self.height_input_str += event.unicode

    def handle_events(self):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.window_width = max(self.MIN_W, event.w)
                self.window_height = max(self.MIN_H, event.h)
                try:
                    self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE | pygame.SCALED | pygame.DOUBLEBUF, vsync=1)
                except TypeError:
                    self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE | pygame.SCALED | pygame.DOUBLEBUF)
                self.ui_scale = min(self.window_width / 1600, self.window_height / 900)
                self.ui.set_fonts(self.ui_scale)
                self.ui.setup_ui()
                self.setup_ui_elements()
                self.vignette_surface = self.create_vignette()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if event.key == pygame.K_DELETE and self.selected_object:
                    self.objects = [obj for obj in self.objects if obj.id != self.selected_object.id]
                    self.selected_object = None
                    self.save_state()
                elif event.key == pygame.K_z and keys[pygame.K_LCTRL]:
                    self.undo()
                elif event.key == pygame.K_y and keys[pygame.K_LCTRL]:
                    self.redo()
                elif event.key == pygame.K_g:
                    self.snap_to_grid = not self.snap_to_grid
                elif event.key == pygame.K_h:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_r and self.selected_object:
                    self.selected_object.rotation += 45
                    self.save_state()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked_ui = False
                    for name, rect in self.ui.buttons.items():
                        if rect.collidepoint(event.pos):
                            clicked_ui = True
                            self.active_button = name
                            break
                    if not clicked_ui:
                        for name, rect in self.ui.toggle_buttons.items():
                            if rect.collidepoint(event.pos):
                                clicked_ui = True
                                self.active_button = name
                                break
                    if not clicked_ui and event.pos[1] > 70 and not self.ar_mode_active:
                        obj = self.get_object_at_mouse(event.pos)
                        if obj:
                            self.selected_object = obj
                            for o in self.objects:
                                o.selected = (o.id == obj.id)
                            self.dragging_object = True
                        else:
                            self.selected_object = None
                            for o in self.objects:
                                o.selected = False
                            self.place_object(event.pos)
                elif event.button == 2:
                    if self.selected_object and not self.ar_mode_active:
                        self.rotating_object = True
                elif event.button == 3:
                    self.dragging_camera = True
                    self.right_click_start = event.pos
                    self.last_mouse_pos = event.pos
                    try:
                        pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_SIZEALL)
                    except Exception:
                        pass
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.active_button:
                        name = self.active_button
                        if self.ui.buttons.get(name) and self.ui.buttons[name].collidepoint(event.pos):
                            if name == "clear":
                                self.objects.clear()
                                self.selected_object = None
                                self.save_state()
                            elif name == "save":
                                self.save_layout()
                            elif name == "screenshot":
                                self.save_screenshot()
                            elif name == "load":
                                self.load_layout()
                            elif name == "undo":
                                self.undo()
                            elif name == "redo":
                                self.redo()
                            elif name == "ar_view":
                                self.ar_mode_active = not self.ar_mode_active
                                if self.ar_mode_active:
                                    self.ar_camera.start()
                                else:
                                    self.ar_camera.stop()
                            elif name == "gen_marker":
                                self.generate_new_marker()
                            else:
                                self.selected_object_type = name
                        elif self.ui.toggle_buttons.get(name) and self.ui.toggle_buttons[name].collidepoint(event.pos):
                            if name == "grid":
                                self.show_grid = not self.show_grid
                            elif name == "snap":
                                self.snap_to_grid = not self.snap_to_grid
                            elif name == "help":
                                self.show_help = not self.show_help
                    if self.dragging_object:
                        self.save_state()
                    self.dragging_object = False
                    self.active_button = None
                elif event.button == 2:
                    if self.rotating_object:
                        self.save_state()
                    self.rotating_object = False
                elif event.button == 3:
                    was_drag = False
                    if self.right_click_start:
                        dx = event.pos[0] - self.right_click_start[0]
                        dy = event.pos[1] - self.right_click_start[1]
                        was_drag = (dx*dx + dy*dy) > 9
                    self.dragging_camera = False
                    self.right_click_start = None
                    try:
                        pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    except Exception:
                        pass
                    if not was_drag:
                        obj = self.get_object_at_mouse(event.pos)
                        if obj:
                            self.objects = [o for o in self.objects if o.id != obj.id]
                            self.selected_object = None
                            self.save_state()
            elif event.type == pygame.MOUSEMOTION:
                if not self.ar_mode_active:
                    self.mouse_world_pos = self.camera.unproject(event.pos[0], event.pos[1], self.window_width, self.window_height, y=0.0)
                if self.dragging_camera:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]
                    self.camera.angle_h = (self.camera.angle_h + dx * 0.5) % 360
                    self.camera.angle_v = max(-85, min(85, self.camera.angle_v - dy * 0.3))
                    self.last_mouse_pos = event.pos
                elif self.dragging_object and self.selected_object and not self.ar_mode_active:
                    world_pos = self.camera.unproject(event.pos[0], event.pos[1], self.window_width, self.window_height, y=0.0)
                    if self.snap_to_grid:
                        world_pos.x = round(world_pos.x / self.GRID_SIZE) * self.GRID_SIZE
                        world_pos.z = round(world_pos.z / self.GRID_SIZE) * self.GRID_SIZE
                    world_pos = self.clamp_to_grid(world_pos)
                    self.selected_object.position.x = world_pos.x
                    self.selected_object.position.z = world_pos.z
                elif self.rotating_object and self.selected_object and not self.ar_mode_active:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    self.selected_object.rotation += dx * 0.5
                    self.last_mouse_pos = event.pos
            elif event.type == pygame.MOUSEWHEEL:
                if keys[pygame.K_LSHIFT] and self.selected_object and not self.ar_mode_active:
                    self.selected_object.scale += event.y * 0.1
                    self.selected_object.scale = max(0.5, min(2.0, self.selected_object.scale))
                else:
                    self.camera.distance = max(200, min(1500, self.camera.distance - event.y * 40))

    def validate_and_start(self):
        try:
            w = float(self.width_input_str)
            d = float(self.depth_input_str)
            h = float(self.height_input_str)
            if w < 8 or d < 8 or h < 8:
                self.setup_error_msg = "Dimensions must be at least 8 feet"
                return
            self.grid_width = int(w * self.UNITS_PER_FOOT)
            self.grid_depth = int(d * self.UNITS_PER_FOOT)
            self.grid_height = int(h * self.UNITS_PER_FOOT)
            self.app_state = "WELCOME"
            max_dim = max(self.grid_width, self.grid_depth, self.grid_height)
            self.camera.distance = max(1100, max_dim * 2.0)
        except ValueError:
            self.setup_error_msg = "Please enter valid numbers."

    def get_object_at_mouse(self, mouse_pos) -> Optional[Object3D]:
        if not self.objects:
            return None
        right, up, fwd, cam_pos = self.camera.get_basis()
        def dist2(o: Object3D):
            dx = o.position.x - cam_pos.x
            dy = o.position.y - cam_pos.y
            dz = o.position.z - cam_pos.z
            return dx*dx + dy*dy + dz*dz
        for obj in sorted(self.objects, key=dist2):
            screen_pt = self.camera.project(obj.position, self.window_width, self.window_height)
            dx = mouse_pos[0] - screen_pt[0]
            dy = mouse_pos[1] - screen_pt[1]
            d = math.hypot(dx, dy)
            base = {"chair": 40, "desk": 60, "table": 80, "podium": 45, "cabinet": 50}.get(obj.obj_type, 40)
            hit_radius = base * obj.scale
            if d <= hit_radius:
                return obj
        return None

    def clamp_to_grid(self, pos: Point3D) -> Point3D:
        hw = self.grid_width / 2
        hd = self.grid_depth / 2
        pos.x = max(-hw, min(hw, pos.x))
        pos.z = max(-hd, min(hd, pos.z))
        return pos

    def place_object(self, mouse_pos):
        world_pos = self.camera.unproject(mouse_pos[0], mouse_pos[1], self.window_width, self.window_height, y=0.0)
        if self.snap_to_grid:
            world_pos.x = round(world_pos.x / self.GRID_SIZE) * self.GRID_SIZE
            world_pos.z = round(world_pos.z / self.GRID_SIZE) * self.GRID_SIZE
        world_pos = self.clamp_to_grid(world_pos)
        default_rotation = 180 if self.selected_object_type == "chair" else 0
        obj = Object3D(
            name=self.selected_object_type,
            position=world_pos,
            rotation=default_rotation,
            obj_type=self.selected_object_type,
            id=self.next_id
        )
        self.next_id += 1
        self.objects.append(obj)
        self.save_state()

    def draw_floor(self):
        hw = self.grid_width / 2
        hd = self.grid_depth / 2
        grid_spacing = self.GRID_SIZE
        floor_world = [Point3D(-hw, 0, -hd), Point3D(hw, 0, -hd), Point3D(hw, 0, hd), Point3D(-hw, 0, hd)]
        floor_screen = [self.camera.project(p, self.window_width, self.window_height) for p in floor_world]
        pygame.draw.polygon(self.screen, (80, 60, 45), floor_screen)
        plank_width = 4 * self.GRID_SIZE
        for x_plank in range(int(-hw // plank_width) * plank_width, int(hw // plank_width) * plank_width + 1, plank_width):
            if x_plank == 0: continue
            p1 = self.camera.project(Point3D(x_plank, 0.5, -hd), self.window_width, self.window_height)
            p2 = self.camera.project(Point3D(x_plank, 0.5, hd), self.window_width, self.window_height)
            try:
                pygame.draw.line(self.screen, (95, 75, 60), p1, p2, 1)
            except Exception:
                pass
        if not self.show_grid:
            return
        grid_color = (70, 82, 99)
        axis_color = (100, 116, 139)
        for x in range(int(-hw // grid_spacing) * grid_spacing, int(hw // grid_spacing) * grid_spacing + 1, grid_spacing):
            if x == 0: continue
            p1 = self.camera.project(Point3D(x, 1.0, -hd), self.window_width, self.window_height)
            p2 = self.camera.project(Point3D(x, 1.0, hd), self.window_width, self.window_height)
            try:
                pygame.draw.aaline(self.screen, grid_color, p1, p2)
            except Exception:
                pass
        for z in range(int(-hd // grid_spacing) * grid_spacing, int(hd // grid_spacing) * grid_spacing + 1, grid_spacing):
            if z == 0: continue
            p1 = self.camera.project(Point3D(-hw, 1.0, z), self.window_width, self.window_height)
            p2 = self.camera.project(Point3D(hw, 1.0, z), self.window_width, self.window_height)
            try:
                pygame.draw.aaline(self.screen, grid_color, p1, p2)
            except Exception:
                pass
        p_x1 = self.camera.project(Point3D(-hw, 1.5, 0), self.window_width, self.window_height)
        p_x2 = self.camera.project(Point3D(hw, 1.5, 0), self.window_width, self.window_height)
        pygame.draw.aaline(self.screen, axis_color, p_x1, p_x2)
        p_z1 = self.camera.project(Point3D(0, 1.5, -hd), self.window_width, self.window_height)
        p_z2 = self.camera.project(Point3D(0, 1.5, hd), self.window_width, self.window_height)
        pygame.draw.aaline(self.screen, axis_color, p_z1, p_z2)

    def draw_walls_and_blackboard(self):
        wall_height = 200
        hw = self.grid_width / 2
        hd = self.grid_depth / 2
        cam_pos = self.camera.get_position()
        if cam_pos.z > -hd + 10:
            back_wall = [Point3D(-hw, 0, -hd), Point3D(hw, 0, -hd), Point3D(hw, wall_height, -hd), Point3D(-hw, wall_height, -hd)]
            self.ui.draw_shaded_polygon(back_wall, (220, 220, 220), (100, 100, 100), 2)
            board_hw = min(hw * 0.8, 400)
            board = [Point3D(-board_hw, 80, -hd + 2), Point3D(board_hw, 80, -hd + 2), Point3D(board_hw, 160, -hd + 2), Point3D(-board_hw, 160, -hd + 2)]
            self.ui.draw_shaded_polygon(board, (26, 26, 26), (0, 0, 0), 3)

    def draw_selection_indicator(self, pos: Point3D, radius: float):
        center = self.camera.project(pos, self.window_width, self.window_height)
        glow = (100, 200, 255)
        for i in range(3):
            pygame.draw.circle(self.screen, glow, center, int(radius + i * 2), 1)
        pygame.draw.circle(self.screen, (59, 130, 246), center, int(radius), 2)

    def draw_objects(self):
        self.draw_walls_and_blackboard()
        right, up, fwd, cam_pos = self.camera.get_basis()
        def cam_z(o: Object3D):
            px = o.position.x - cam_pos.x
            py = o.position.y - cam_pos.y
            pz = o.position.z - cam_pos.z
            return px * fwd.x + py * fwd.y + pz * fwd.z
        for obj in sorted(self.objects, key=lambda o: cam_z(o), reverse=True):
            drawer = {
                "chair": self.ui.draw_chair,
                "desk": self.ui.draw_desk,
                "table": self.ui.draw_table,
                "podium": self.ui.draw_podium,
                "cabinet": self.ui.draw_cabinet
            }.get(obj.obj_type)
            if drawer:
                drawer(obj, self)

    def draw_setup_screen(self):
        self.screen.fill((15, 23, 42))
        title = self.ui.large_font.render("Enter Room Dimensions", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.window_width//2, self.width_input_rect.top - 80)))
        self.ui.draw_input(self, self.width_input_rect, "Width (ft):", self.width_input_str, "WIDTH")
        self.ui.draw_input(self, self.depth_input_rect, "Depth (ft):", self.depth_input_str, "DEPTH")
        self.ui.draw_input(self, self.height_input_rect, "Height (ft):", self.height_input_str, "HEIGHT")
        mouse_pos = pygame.mouse.get_pos()
        if self.active_button == "START":
            c = (22, 163, 74)
        elif self.start_button_rect.collidepoint(mouse_pos):
            c = (52, 211, 153)
        else:
            c = (34, 197, 94)
        pygame.draw.rect(self.screen, c, self.start_button_rect, border_radius=8)
        btn_text = self.ui.font.render("Generate Room", True, (255, 255, 255))
        self.screen.blit(btn_text, btn_text.get_rect(center=self.start_button_rect.center))
        if self.setup_error_msg:
            err = self.ui.small_font.render(self.setup_error_msg, True, (220, 38, 38))
            self.screen.blit(err, err.get_rect(center=(self.window_width//2, self.start_button_rect.bottom + 30)))
        pygame.display.flip()

    def generate_new_marker(self):
        """
        Generates a new AruCo marker image and saves it to a file.
        """
        marker_id = self.next_marker_id
        marker_size = 400
        filename = f"marker_{marker_id}.png"
        
        print(f"Generating marker ID {marker_id}...")
        
        try:
            marker_image = np.zeros((marker_size, marker_size), dtype=np.uint8)
            
            marker_image = aruco.generateImageMarker(
                self.aruco_dict, marker_id, marker_size, marker_image, 1
            )
            
            cv2.imwrite(filename, marker_image)
            
            print(f"--- Successfully saved new marker to {filename} ---")
            print(f"You can now print this file or show it on your phone.")
            
            self.next_marker_id += 1
            
        except Exception as e:
            print(f"Error generating marker: {e}")

    def draw_ar_view(self):
        """
        Gets the camera frame, runs AruCo detection, and draws the result (with virtual objects).
        """
        frame = self.ar_camera.get_frame()
        
        if frame is not None:
            # 1. Flip horizontally 
            frame = cv2.flip(frame, 1)

            # 2. Run AruCo Marker Detection
            corners, ids, _ = self.aruco_detector.detectMarkers(frame)

            # 3. Draw on the frame IF a marker is found (Object Mapping)
            if ids is not None:
                for i, marker_id in enumerate(ids):
                    marker_id_num = marker_id[0]
                    
                    object_type = None
                    object_color = (0, 0, 0) # Default BGR color
                    
                    # --- MAPPING MARKER ID TO OBJECT TYPE ---
                    if marker_id_num == 23:
                        object_type = "Desk"
                        object_color = (255, 100, 0) # Blue
                    elif marker_id_num == 24:
                        object_type = "Chair"
                        object_color = (0, 0, 255) # Red
                    elif marker_id_num == 25:
                        object_type = "Cabinet"
                        object_color = (0, 255, 255) # Yellow
                    # ----------------------------------------

                    # Only draw if this is an ID we recognize
                    if object_type is not None:
                        # Get the 4 corner points
                        marker_corners = corners[i][0]
                        int_corners = np.int32(marker_corners)
                        
                        # Draw a green border
                        cv2.polylines(frame, [int_corners], True, (0, 255, 0), 2)
                        
                        # Draw the "object" with the correct color
                        overlay = frame.copy()
                        cv2.fillPoly(overlay, [int_corners], object_color)
                        alpha = 0.5 # 50% transparency
                        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
                        
                        # Draw the text with the correct object type
                        tl = int_corners[0]
                        cv2.putText(frame, f"Object: {object_type} (ID: {marker_id_num})", 
                                    (tl[0], tl[1] - 15), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 
                                    0.6, (0, 255, 0), 2)

            # 4. Convert OpenCV frame (BGR) to Pygame surface (RGB)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            frame_height, frame_width = frame.shape[:2]
            
            frame_surface = pygame.image.frombuffer(
                frame.tobytes(), (frame_width, frame_height), "RGB"
            )
            
            scaled_frame = pygame.transform.scale(
                frame_surface, (self.window_width, self.window_height)
            )
            
            self.screen.blit(scaled_frame, (0, 0))
            
            # 5. Draw UI on top
            self.ui.draw_ui(self) 
            
            # Add a help label
            label_text = "AR View Active (Using Marker ID 23-25)"
            label = self.ui.font.render(label_text, True, self.ui.WHITE)
            shadow = self.ui.font.render(label_text, True, self.ui.BLACK)
            rect = label.get_rect(center=(self.window_width // 2, self.window_height - 30))
            
            self.screen.blit(shadow, (rect.x + 2, rect.y + 2))
            self.screen.blit(label, rect)
        else:
            # Camera starting screen
            self.screen.fill((10, 10, 10))
            label = self.ui.font.render("Starting Camera...", True, self.ui.WHITE)
            rect = label.get_rect(center=(self.window_width // 2, self.window_height // 2))
            self.screen.blit(label, rect)
            self.ui.draw_ui(self)

    def draw_welcome_screen(self):
        original_h, original_v, original_dist = self.camera.angle_h, self.camera.angle_v, self.camera.distance
        self.camera.angle_h = 45
        self.camera.angle_v = 35
        max_dim = max(self.grid_width, self.grid_depth, self.grid_height)
        self.camera.distance = max(1200, max_dim * 2.2)
        self.screen.fill((15, 23, 42))
        self.ui.draw_shaded_polygon([Point3D(-9000,0,-9000), Point3D(9000,0,-9000), Point3D(9000,0,9000), Point3D(-9000,0,9000)], (35, 45, 35))
        hw = self.grid_width / 2
        hd = self.grid_depth / 2
        h = self.grid_height
        right_wall = [Point3D(hw, 0, -hd), Point3D(hw, 0, hd), Point3D(hw, h, hd), Point3D(hw, h, -hd)]
        self.ui.draw_shaded_polygon(right_wall, (200, 190, 180), (50,50,50), 2)
        front_wall = [Point3D(-hw, 0, hd), Point3D(hw, 0, hd), Point3D(hw, h, hd), Point3D(-hw, h, hd)]
        self.ui.draw_shaded_polygon(front_wall, (200, 190, 180), (50,50,50), 2)
        oh = 15
        rt = 15
        self.ui.draw_shaded_polygon([Point3D(-hw-oh, h, hd+oh), Point3D(hw+oh, h, hd+oh), Point3D(hw+oh, h+rt, hd+oh), Point3D(-hw-oh, h+rt, hd+oh)], (60, 60, 70))
        self.ui.draw_shaded_polygon([Point3D(hw+oh, h, -hd-oh), Point3D(hw+oh, h, hd+oh), Point3D(hw+oh, h+rt, hd+oh), Point3D(hw+oh, h+rt, -hd-oh)], (60, 60, 70))
        roof_top = [Point3D(-hw-oh, h+rt, -hd-oh), Point3D(hw+oh, h+rt, -hd-oh), Point3D(hw+oh, h+rt, hd+oh), Point3D(-hw-oh, h+rt, hd+oh)]
        self.ui.draw_shaded_polygon(roof_top, (80, 85, 95), (0,0,0), 2)
        door_w, door_h = 100, min(160, h - 10)
        door_x = 0
        hinge = Point3D(door_x - door_w/2, 0, hd + 2)
        rad = math.radians(self.door_angle)
        def rot_door(dx, dz):
            return Point3D(hinge.x + dx * math.cos(rad) - dz * math.sin(rad), 0, hinge.z + dx * math.sin(rad) + dz * math.cos(rad))
        door_poly = [
            Point3D(hinge.x, 0, hinge.z),
            rot_door(door_w, 0),
            rot_door(door_w, 0),
            Point3D(hinge.x, door_h, hinge.z)
        ]
        door_poly[2].y = door_h
        frame_w = door_w + 10
        frame_h = door_h + 5
        frame = [Point3D(door_x - frame_w/2, 0, hd+1), Point3D(door_x + frame_w/2, 0, hd+1),
                 Point3D(door_x + frame_w/2, frame_h, hd+1), Point3D(door_x - frame_w/2, frame_h, hd+1)]
        self.ui.draw_shaded_polygon(frame, (80, 60, 45), (0,0,0), 1)
        mouse_pos = pygame.mouse.get_pos()
        p1_2d = self.camera.project(door_poly[0], self.window_width, self.window_height)
        p2_2d = self.camera.project(door_poly[2], self.window_width, self.window_height)
        min_x, max_x = min(p1_2d[0], p2_2d[0]), max(p1_2d[0], p2_2d[0])
        min_y, max_y = min(p2_2d[1], p1_2d[1]), max(p2_2d[1], p1_2d[1])
        self.is_hovering_door = (min_x <= mouse_pos[0] <= max_x and min_y <= mouse_pos[1] <= max_y)
        door_color = (100, 70, 50) if not self.is_hovering_door else (140, 100, 80)
        self.ui.draw_shaded_polygon(door_poly, door_color, (30,20,10), 2)
        if self.door_angle < 80:
            knob_pos = rot_door(door_w - 15, -5)
            knob_pos.y = door_h / 2
            knob_2d = self.camera.project(knob_pos, self.window_width, self.window_height)
            pygame.draw.circle(self.screen, (255, 215, 0), knob_2d, int(5 * self.ui_scale))
        if self.door_angle < 10:
            msg = self.ui.large_font.render("Click the door to enter", True, (255, 255, 255))
            msg_rect = msg.get_rect(center=(self.window_width//2, self.window_height - 120))
            shadow = self.ui.large_font.render("Click the door to enter", True, (0, 0, 0))
            self.screen.blit(shadow, (msg_rect.x+2, msg_rect.y+2))
            self.screen.blit(msg, msg_rect)
        if self.app_state == "OPENING":
            self.door_angle += (100 - self.door_angle) * 0.06
            if self.door_angle > 95:
                self.app_state = "RUNNING"
                self.ui.setup_ui()
        self.camera.angle_h, self.camera.angle_v, self.camera.distance = original_h, original_v, original_dist
        pygame.display.flip()

    def save_layout(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = "layouts"
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            filename = os.path.join(save_dir, f"classroom_layout_{timestamp}.json")
            data = {
                "version": "2.1",
                "timestamp": timestamp,
                "camera": {
                    "distance": self.camera.distance,
                    "angle_h": self.camera.angle_h,
                    "angle_v": self.camera.angle_v
                },
                "grid": {
                    "width": self.grid_width,
                    "depth": self.grid_depth
                },
                "objects": [
                    {
                        "id": obj.id,
                        "type": obj.obj_type,
                        "name": obj.name,
                        "position": {"x": obj.position.x, "y": obj.position.y, "z": obj.position.z},
                        "rotation": obj.rotation,
                        "scale": obj.scale
                    }
                    for obj in self.objects
                ]
            }
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Layout DATA saved to {filename}")
        except Exception as e:
            print(f"Error saving layout data: {e}")

    def save_screenshot(self):
        print("Attempting to save screenshot...")
        save_dir = "layouts"
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(save_dir, f"screenshot_{timestamp}.jpg")
            pygame.image.save(self.screen, filename)
            print(f"Screenshot saved to {filename}")
        except Exception as e:
            print(f"Error saving screenshot: {e}")

    def load_layout(self):
        try:
            files = [f for f in os.listdir("layouts") if f.startswith("classroom_layout_") and f.endswith(".json")]
            if not files:
                print("No saved layouts found")
                return
            latest_file = max(files)
            filepath = os.path.join("layouts", latest_file)
            with open(filepath, "r") as f:
                data = json.load(f)
            if "camera" in data:
                self.camera.distance = data["camera"].get("distance", 700)
                self.camera.angle_h = data["camera"].get("angle_h", 45)
                self.camera.angle_v = data["camera"].get("angle_v", 35)
            if "grid" in data:
                self.grid_width = data["grid"].get("width", 600)
                self.grid_depth = data["grid"].get("depth", 600)
            else:
                self.grid_width = 600
                self.grid_depth = 600
            self.objects.clear()
            for obj_data in data["objects"]:
                obj = Object3D(
                    id=obj_data["id"],
                    name=obj_data["name"],
                    obj_type=obj_data["type"],
                    position=Point3D(**obj_data["position"]),
                    rotation=obj_data["rotation"],
                    scale=obj_data.get("scale", 1.0)
                )
                self.objects.append(obj)
                self.next_id = max(self.next_id, obj.id + 1)
            self.selected_object = None
            self.save_state()
            print(f"Layout loaded from {filepath}")
        except Exception as e:
            print(f"Error loading layout: {e}")

    def run(self):
        while self.running:
            if self.app_state == "SETUP":
                self.handle_setup_events()
                self.draw_setup_screen()
            elif self.app_state in ["WELCOME", "OPENING"]:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self.window_width = max(self.MIN_W, event.w)
                        self.window_height = max(self.MIN_H, event.h)
                        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE | pygame.SCALED | pygame.DOUBLEBUF)
                        self.ui_scale = min(self.window_width / 1600, self.window_height / 900)
                        self.ui.set_fonts(self.ui_scale)
                        self.ui.setup_ui()
                        self.setup_ui_elements()
                        self.vignette_surface = self.create_vignette()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1 and hasattr(self, 'is_hovering_door') and self.is_hovering_door:
                            self.app_state = "OPENING"
                self.draw_welcome_screen()
            elif self.app_state == "RUNNING":
                self.handle_events()
                
                if self.ar_mode_active:
                    self.draw_ar_view()
                else:
                    self.screen.fill((15, 23, 42))
                    self.draw_floor()
                    self.draw_objects()
                    self.ui.draw_ui(self)
                    self.screen.blit(self.vignette_surface, (0, 0))
                
                pygame.display.flip()
            self.clock.tick(self.FPS)
        
        if self.ar_camera.is_running():
            self.ar_camera.stop()
            
        pygame.quit()
        print("\nExited AR Classroom Planner.")