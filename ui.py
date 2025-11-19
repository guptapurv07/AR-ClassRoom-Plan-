import pygame
import math
from objects import Point3D

class UI:
    def __init__(self, app):
        self.app = app
        self.WOOD_COLOR = (80, 60, 45)
        self.DARK_WOOD = (65, 45, 30)
        self.FLOOR_COLOR = (80, 60, 45)
        self.PLANK_COLOR = (95, 75, 60)
        self.WALL_COLOR = (220, 220, 220)
        self.BLACKBOARD_COLOR = (26, 26, 26)
        self.BUTTON_ACTIVE = (59, 130, 246)
        self.BUTTON_INACTIVE = (75, 85, 99)
        self.BUTTON_HOVER = (107, 114, 128)
        self.BUTTON_PRESSED = (55, 65, 81)
        self.RED = (220, 38, 38)
        self.RED_HOVER = (239, 68, 68)
        self.RED_PRESSED = (185, 28, 28)
        self.GREEN = (34, 197, 94)
        self.GREEN_HOVER = (52, 211, 153)
        self.GREEN_PRESSED = (22, 163, 74)
        self.BLUE = (59, 130, 246)
        self.BLUE_HOVER = (96, 165, 250)
        self.BLUE_PRESSED = (29, 78, 216)
        self.ORANGE = (249, 115, 22)
        self.ORANGE_HOVER = (251, 146, 60)
        self.ORANGE_PRESSED = (202, 138, 4)
        self.SELECTION_COLOR = (59, 130, 246)
        self.GLOW_COLOR = (100, 200, 255)
        self.YELLOW = (234, 179, 8)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.font = None
        self.small_font = None
        self.tiny_font = None
        self.large_font = None
        self.buttons = {}
        self.toggle_buttons = {}
        self.set_fonts(1.0)

    def set_fonts(self, scale):
        base = max(0.75, min(1.5, scale))
        font_name = "Calibri" if "Calibri" in pygame.font.get_fonts() else "Arial"
        self.font = pygame.font.SysFont(font_name, max(18, int(28 * base)), bold=True)
        self.small_font = pygame.font.SysFont(font_name, max(14, int(22 * base)))
        self.tiny_font = pygame.font.SysFont(font_name, max(12, int(18 * base)))
        self.large_font = pygame.font.SysFont(font_name, max(24, int(42 * base)), bold=True)

    def setup_ui(self):
        padding = int(10 * self.app.ui_scale)
        button_height = int(40 * self.app.ui_scale)
        button_width = int(80 * self.app.ui_scale)
        gap = int(10 * self.app.ui_scale)
        x_offset = padding
        self.buttons = {
            "chair": pygame.Rect(x_offset, padding, button_width, button_height),
        }
        x_offset += button_width + gap
        self.buttons["desk"] = pygame.Rect(x_offset, padding, button_width, button_height)
        x_offset += button_width + gap
        self.buttons["table"] = pygame.Rect(x_offset, padding, button_width, button_height)
        x_offset += button_width + gap
        self.buttons["podium"] = pygame.Rect(x_offset, padding, button_width, button_height)
        x_offset += button_width + gap
        self.buttons["cabinet"] = pygame.Rect(x_offset, padding, button_width, button_height)
        
        # Action buttons on the right
        x_offset = self.app.window_width - padding - button_width
        self.buttons["save"] = pygame.Rect(x_offset, padding, button_width, button_height)
        x_offset -= button_width + gap
        self.buttons["screenshot"] = pygame.Rect(x_offset, padding, button_width, button_height)
        x_offset -= button_width + gap
        self.buttons["load"] = pygame.Rect(x_offset, padding, button_width, button_height)
        x_offset -= button_width + gap
        self.buttons["clear"] = pygame.Rect(x_offset, padding, button_width, button_height)
        
        # Undo/Redo buttons
        x_offset -= button_width + (gap * 3)
        self.buttons["redo"] = pygame.Rect(x_offset, padding, button_width, button_height)
        x_offset -= button_width + gap
        self.buttons["undo"] = pygame.Rect(x_offset, padding, button_width, button_height)

        # --- NEW AR BUTTONS ---
        x_offset -= button_width + (gap * 2) 
        self.buttons["ar_view"] = pygame.Rect(x_offset, padding, button_width, button_height)
        x_offset -= button_width + gap
        self.buttons["gen_marker"] = pygame.Rect(x_offset, padding, button_width, button_height)
        # ----------------------
        
        toggle_width = int(90 * self.app.ui_scale)
        toggle_height = int(35 * self.app.ui_scale)
        toggle_x = self.app.window_width - toggle_width - padding
        self.toggle_buttons = {
            "grid": pygame.Rect(toggle_x, self.app.window_height - 140 * self.app.ui_scale, toggle_width, toggle_height),
            "snap": pygame.Rect(toggle_x, self.app.window_height - 100 * self.app.ui_scale, toggle_width, toggle_height),
            "help": pygame.Rect(toggle_x, self.app.window_height - 60 * self.app.ui_scale, toggle_width, toggle_height),
        }

    def draw_shaded_polygon(self, points_3d, color, edge_color=(0,0,0), edge_width=0):
        if len(points_3d) < 3: return
        LIGHT_VEC = Point3D(-0.5, 1.2, -0.8).normalize()
        AMBIENT_LIGHT = 0.4
        p0, p1, p2 = points_3d[0], points_3d[1], points_3d[2]
        v1 = p1 - p0
        v2 = p2 - p0
        normal = v1.cross(v2).normalize()
        diffuse = max(0, normal.dot(LIGHT_VEC))
        intensity = AMBIENT_LIGHT + diffuse * (1.0 - AMBIENT_LIGHT)
        intensity = max(0.0, min(1.0, intensity))
        r, g, b = color[:3]
        shaded_color = (int(r * intensity), int(g * intensity), int(b * intensity))
        screen_points = [self.app.camera.project(p, self.app.window_width, self.app.window_height) for p in points_3d]
        pygame.draw.polygon(self.app.screen, shaded_color, screen_points)
        if edge_width > 0 and edge_color is not None:
            pygame.draw.polygon(self.app.screen, edge_color, screen_points, edge_width)

    def draw_chair(self, obj, app):
        pos = obj.position
        scale = obj.scale
        rot = math.radians(obj.rotation)
        def r2(x, z):
            return (x * math.cos(rot) - z * math.sin(rot), x * math.sin(rot) + z * math.cos(rot))
        s = 20 * scale
        seat_pts = [
            Point3D(pos.x + r2(-s, -s)[0], pos.y + 25 * scale, pos.z + r2(-s, -s)[1]),
            Point3D(pos.x + r2(s, -s)[0], pos.y + 25 * scale, pos.z + r2(s, -s)[1]),
            Point3D(pos.x + r2(s, s)[0], pos.y + 25 * scale, pos.z + r2(s, s)[1]),
            Point3D(pos.x + r2(-s, s)[0], pos.y + 25 * scale, pos.z + r2(-s, s)[1]),
        ]
        self.draw_shaded_polygon(seat_pts, self.WOOD_COLOR, self.BLACK, 2)
        back_z = -22 * scale
        back_pts = [
            Point3D(pos.x + r2(-s, back_z)[0], pos.y + 25 * scale, pos.z + r2(-s, back_z)[1]),
            Point3D(pos.x + r2(s, back_z)[0], pos.y + 25 * scale, pos.z + r2(s, back_z)[1]),
            Point3D(pos.x + r2(s, back_z)[0], pos.y + 60 * scale, pos.z + r2(s, back_z)[1]),
            Point3D(pos.x + r2(-s, back_z)[0], pos.y + 60 * scale, pos.z + r2(-s, back_z)[1]),
        ]
        self.draw_shaded_polygon(back_pts, self.DARK_WOOD, self.BLACK, 2)
        for dx, dz in [(-15, -15), (15, -15), (-15, 15), (15, 15)]:
            rx, rz = r2(dx * scale, dz * scale)
            top = app.camera.project(Point3D(pos.x + rx, pos.y + 25 * scale, pos.z + rz), app.window_width, app.window_height)
            bot = app.camera.project(Point3D(pos.x + rx, pos.y, pos.z + rz), app.window_width, app.window_height)
            pygame.draw.line(app.screen, self.DARK_WOOD, top, bot, max(1, int(3 * scale)))
        if obj.selected:
            app.draw_selection_indicator(pos, 35 * scale)

    def draw_desk(self, obj, app):
        pos = obj.position
        scale = obj.scale
        rot = math.radians(obj.rotation)
        def r2(x, z): return (x * math.cos(rot) - z * math.sin(rot), x * math.sin(rot) + z * math.cos(rot))
        corners = [(-40, -25), (40, -25), (40, 25), (-40, 25)]
        pts = [Point3D(pos.x + r2(x * scale, z * scale)[0], pos.y + 35 * scale, pos.z + r2(x * scale, z * scale)[1]) for x, z in corners]
        scr = [app.camera.project(p, app.window_width, app.window_height) for p in pts]
        pygame.draw.polygon(app.screen, self.WOOD_COLOR, scr)
        pygame.draw.polygon(app.screen, self.BLACK, scr, 2)
        for dx, dz in [(-35, -20), (35, -20), (-35, 20), (35, 20)]:
            rx, rz = r2(dx * scale, dz * scale)
            top = app.camera.project(Point3D(pos.x + rx, pos.y + 35 * scale, pos.z + rz), app.window_width, app.window_height)
            bot = app.camera.project(Point3D(pos.x + rx, pos.y, pos.z + rz), app.window_width, app.window_height)
            pygame.draw.line(app.screen, self.DARK_WOOD, top, bot, max(1, int(4 * scale)))
        if obj.selected:
            app.draw_selection_indicator(pos, 50 * scale)

    def draw_table(self, obj, app):
        pos = obj.position
        scale = obj.scale
        rot = math.radians(obj.rotation)
        def r2(x, z): return (x * math.cos(rot) - z * math.sin(rot), x * math.sin(rot) + z * math.cos(rot))
        corners = [(-60, -40), (60, -40), (60, 40), (-60, 40)]
        pts = [Point3D(pos.x + r2(x * scale, z * scale)[0], pos.y + 40 * scale, pos.z + r2(x * scale, z * scale)[1]) for x, z in corners]
        scr = [app.camera.project(p, app.window_width, app.window_height) for p in pts]
        pygame.draw.polygon(app.screen, self.WOOD_COLOR, scr)
        pygame.draw.polygon(app.screen, self.BLACK, scr, 2)
        for dx, dz in [(-50, -30), (50, -30), (-50, 30), (50, 30)]:
            rx, rz = r2(dx * scale, dz * scale)
            top = app.camera.project(Point3D(pos.x + rx, pos.y + 40 * scale, pos.z + rz), app.window_width, app.window_height)
            bot = app.camera.project(Point3D(pos.x + rx, pos.y, pos.z + rz), app.window_width, app.window_height)
            pygame.draw.line(app.screen, self.DARK_WOOD, top, bot, max(1, int(5 * scale)))
        if obj.selected:
            app.draw_selection_indicator(pos, 70 * scale)

    def draw_podium(self, obj, app):
        pos = obj.position
        scale = obj.scale
        rot = math.radians(obj.rotation)
        def r2(x, z):
            return (x * math.cos(rot) - z * math.sin(rot), x * math.sin(rot) + z * math.cos(rot))
        w, d, h = 20 * scale, 15 * scale, 60 * scale
        front = [
            Point3D(pos.x + r2(-w, d)[0], pos.y, pos.z + r2(-w, d)[1]),
            Point3D(pos.x + r2(w, d)[0], pos.y, pos.z + r2(w, d)[1]),
            Point3D(pos.x + r2(w, d)[0], pos.y + h, pos.z + r2(w, d)[1]),
            Point3D(pos.x + r2(-w, d)[0], pos.y + h, pos.z + r2(-w, d)[1]),
        ]
        self.draw_shaded_polygon(front, self.DARK_WOOD, self.BLACK, 2)
        left = [
            Point3D(pos.x + r2(-w, -d)[0], pos.y, pos.z + r2(-w, -d)[1]),
            Point3D(pos.x + r2(-w, d)[0], pos.y, pos.z + r2(-w, d)[1]),
            Point3D(pos.x + r2(-w, d)[0], pos.y + h, pos.z + r2(-w, d)[1]),
            Point3D(pos.x + r2(-w, -d)[0], pos.y + h, pos.z + r2(-w, -d)[1]),
        ]
        self.draw_shaded_polygon(left, self.DARK_WOOD, self.BLACK, 2)
        tw, td = w + 5 * scale, d + 5 * scale
        h_high = h + 12 * scale
        h_low = h + 2 * scale
        top_surface = [
            Point3D(pos.x + r2(-tw, -td)[0], pos.y + h_high, pos.z + r2(-tw, -td)[1]),
            Point3D(pos.x + r2(tw, -td)[0], pos.y + h_high, pos.z + r2(tw, -td)[1]),
            Point3D(pos.x + r2(tw, td)[0], pos.y + h_low, pos.z + r2(tw, td)[1]),
            Point3D(pos.x + r2(-tw, td)[0], pos.y + h_low, pos.z + r2(-tw, td)[1]),
        ]
        self.draw_shaded_polygon(top_surface, self.WOOD_COLOR, self.BLACK, 2)
        top_front_lip = [
            Point3D(pos.x + r2(-tw, -td)[0], pos.y + h, pos.z + r2(-tw, -td)[1]),
            Point3D(pos.x + r2(tw, -td)[0], pos.y + h, pos.z + r2(tw, -td)[1]),
            Point3D(pos.x + r2(tw, -td)[0], pos.y + h_high, pos.z + r2(tw, -td)[1]),
            Point3D(pos.x + r2(-tw, -td)[0], pos.y + h_high, pos.z + r2(-tw, -td)[1]),
        ]
        self.draw_shaded_polygon(top_front_lip, self.DARK_WOOD, self.BLACK, 2)
        if obj.selected:
            app.draw_selection_indicator(pos, 35 * scale)

    def draw_cabinet(self, obj, app):
        pos = obj.position
        scale = obj.scale
        rot = math.radians(obj.rotation)
        def r2(x, z): return (x * math.cos(rot) - z * math.sin(rot), x * math.sin(rot) + z * math.cos(rot))
        w, d, h = 35 * scale, 20 * scale, 70 * scale
        top_pts = [
            Point3D(pos.x + r2(-w, -d)[0], pos.y + h, pos.z + r2(-w, -d)[1]),
            Point3D(pos.x + r2(w, -d)[0], pos.y + h, pos.z + r2(w, -d)[1]),
            Point3D(pos.x + r2(w, d)[0], pos.y + h, pos.z + r2(w, d)[1]),
            Point3D(pos.x + r2(-w, d)[0], pos.y + h, pos.z + r2(-w, d)[1]),
        ]
        self.draw_shaded_polygon(top_pts, self.DARK_WOOD, self.BLACK, 2)
        front_pts = [
            Point3D(pos.x + r2(-w, d)[0], pos.y, pos.z + r2(-w, d)[1]),
            Point3D(pos.x + r2(w, d)[0], pos.y, pos.z + r2(w, d)[1]),
            Point3D(pos.x + r2(w, d)[0], pos.y + h, pos.z + r2(w, d)[1]),
            Point3D(pos.x + r2(-w, d)[0], pos.y + h, pos.z + r2(-w, d)[1]),
        ]
        self.draw_shaded_polygon(front_pts, self.WOOD_COLOR, self.BLACK, 2)
        left_pts = [
            Point3D(pos.x + r2(-w, -d)[0], pos.y, pos.z + r2(-w, -d)[1]),
            Point3D(pos.x + r2(-w, d)[0], pos.y, pos.z + r2(-w, d)[1]),
            Point3D(pos.x + r2(-w, d)[0], pos.y + h, pos.z + r2(-w, d)[1]),
            Point3D(pos.x + r2(-w, -d)[0], pos.y + h, pos.z + r2(-w, -d)[1]),
        ]
        self.draw_shaded_polygon(left_pts, self.DARK_WOOD, self.BLACK, 2)
        right_pts = [
            Point3D(pos.x + r2(w, d)[0], pos.y, pos.z + r2(w, d)[1]),
            Point3D(pos.x + r2(w, -d)[0], pos.y, pos.z + r2(w, -d)[1]),
            Point3D(pos.x + r2(w, -d)[0], pos.y + h, pos.z + r2(w, -d)[1]),
            Point3D(pos.x + r2(w, d)[0], pos.y + h, pos.z + r2(w, d)[1]),
        ]
        self.draw_shaded_polygon(right_pts, self.DARK_WOOD, self.BLACK, 2)
        if obj.selected:
            app.draw_selection_indicator(pos, 40 * scale)

    def draw_ui(self, app):
        panel_surface = pygame.Surface((app.window_width, int(70 * app.ui_scale)), pygame.SRCALPHA)
        h = panel_surface.get_height()
        for y in range(h):
            c = 20 + y // 2
            pygame.draw.line(panel_surface, (c, c, c + 10, 235), (0, y), (app.window_width, y))
        app.screen.blit(panel_surface, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        for name, rect in self.buttons.items():
            is_selected = name == app.selected_object_type
            is_hover = rect.collidepoint(mouse_pos)
            is_active = app.active_button == name
            
            # Action buttons color logic
            if name in ["clear", "save", "load", "undo", "redo", "screenshot"]:
                if name == "clear":
                    base, hover, press = self.RED, self.RED_HOVER, self.RED_PRESSED
                elif name == "save":
                    base, hover, press = self.GREEN, self.GREEN_HOVER, self.GREEN_PRESSED
                elif name == "load":
                    base, hover, press = self.BLUE, self.BLUE_HOVER, self.BLUE_PRESSED
                elif name == "screenshot":
                    base, hover, press = (0, 150, 136), (38, 166, 154), (0, 121, 107)
                else:
                    base, hover, press = self.ORANGE, self.ORANGE_HOVER, self.ORANGE_PRESSED
                if is_active: color = press
                elif is_hover: color = hover
                else: color = base

            # --- AR BUTTONS COLOR LOGIC (Custom Colors) ---
            elif name == "ar_view":
                base, hover, press = (147, 51, 234), (168, 85, 247), (126, 34, 206) # Purple
                if is_active: color = press
                elif app.ar_mode_active: color = self.BUTTON_ACTIVE # Blue when active
                elif is_hover: color = hover
                else: color = base
            elif name == "gen_marker":
                base, hover, press = (192, 132, 252), (216, 180, 254), (167, 139, 250) # Light Purple
                if is_active: color = press
                elif is_hover: color = hover
                else: color = base
            # ----------------------------------------------
                
            # Object selection buttons color logic
            else:
                if is_active: color = self.BUTTON_PRESSED
                elif is_selected: color = self.BUTTON_ACTIVE
                elif is_hover: color = self.BUTTON_HOVER
                else: color = self.BUTTON_INACTIVE
                
            pygame.draw.rect(app.screen, color, rect, border_radius=8)
            if is_selected:
                glow_rect = rect.inflate(4, 4)
                pygame.draw.rect(app.screen, self.GLOW_COLOR, glow_rect, border_radius=10, width=2)
            
            # --- LABEL TEXT LOGIC ---
            label = name.capitalize()
            if name == "screenshot": label = "Shot"
            if name == "ar_view": label = "AR Cam"
            if name == "gen_marker": label = "Gen Marker"
            # ------------------------
            
            text_surf = self.small_font.render(label, True, self.WHITE)
            text_rect = text_surf.get_rect(center=rect.center)
            app.screen.blit(text_surf, text_rect)
            
        for name, rect in self.toggle_buttons.items():
            is_hover = rect.collidepoint(mouse_pos)
            is_active_toggle = (name == "grid" and app.show_grid) or (name == "snap" and app.snap_to_grid) or (name == "help" and app.show_help)
            is_pressed = app.active_button == name
            if is_pressed: color = self.BUTTON_PRESSED
            elif is_active_toggle: color = self.BUTTON_ACTIVE
            elif is_hover: color = self.BUTTON_HOVER
            else: color = self.BUTTON_INACTIVE
            pygame.draw.rect(app.screen, color, rect, border_radius=8)
            text = self.tiny_font.render(name.capitalize(), True, self.WHITE)
            text_rect = text.get_rect(center=rect.center)
            app.screen.blit(text, text_rect)
        
        count_text = self.small_font.render(f"Objects: {len(app.objects)}", True, self.WHITE)
        app.screen.blit(count_text, (int(10 * app.ui_scale), app.window_height - int(35 * app.ui_scale)))
        
        if app.selected_object and not app.ar_mode_active:
            info_y = 80
            info_x = 10
            pos_x_ft = app.selected_object.position.x / app.UNITS_PER_FOOT
            pos_z_ft = app.selected_object.position.z / app.UNITS_PER_FOOT
            info_texts = [
                f"Selected: {app.selected_object.obj_type.capitalize()} (ID: {app.selected_object.id})",
                f"Position: {pos_x_ft:.1f}' , {pos_z_ft:.1f}'",
                f"Rotation: {app.selected_object.rotation:.0f} degrees",
                f"Scale: {app.selected_object.scale:.1f}x",
            ]
            for text_str in info_texts:
                text = self.tiny_font.render(text_str, True, self.WHITE)
                shadow = self.tiny_font.render(text_str, True, self.BLACK)
                app.screen.blit(shadow, (info_x + 1, info_y + 1))
                app.screen.blit(text, (info_x, info_y))
                info_y += 20
        
        if app.show_help and not app.ar_mode_active:
            self.draw_help_overlay(app)

    def draw_input(self, app, rect, label_text, value_text, active_name):
        label = self.font.render(label_text, True, self.WHITE)
        app.screen.blit(label, (rect.x, rect.y - 45))
        is_active = (app.active_input == active_name)
        color = self.BLUE if is_active else (100, 100, 100)
        pygame.draw.rect(app.screen, (240, 240, 240), rect)
        pygame.draw.rect(app.screen, color, rect, 3)
        show_cursor = is_active and (pygame.time.get_ticks() // 500) % 2 == 0
        display_text = value_text + ("|" if show_cursor else "")
        text_surf = self.font.render(display_text, True, self.BLACK)
        app.screen.blit(text_surf, (rect.x + 10, rect.centery - text_surf.get_height()//2))

    def draw_help_overlay(self, app):
        overlay = pygame.Surface((500, 500))
        overlay.set_alpha(240)
        overlay.fill((30, 30, 30))
        x = app.window_width // 2 - 250
        y = app.window_height // 2 - 250
        app.screen.blit(overlay, (x, y))
        pygame.draw.rect(app.screen, self.BLUE, pygame.Rect(x, y, 500, 500), 3, border_radius=10)
        title = self.font.render("Keyboard & Mouse Controls", True, self.WHITE)
        app.screen.blit(title, (x + 100, y + 20))
        help_texts = [
            "",
            "MOUSE CONTROLS:",
            " Left Click: Place/Select object",
            " Left Drag: Move selected object",
            " Right Click: Delete object / Rotate view",
            " Right Drag: Rotate camera 360 degrees",
            " Mouse Wheel: Zoom in/out",
            " Shift + Wheel: Scale selected object",
            "",
            "KEYBOARD SHORTCUTS:",
            " Delete: Remove selected object",
            " R: Rotate selected object 45 degrees",
            " G: Toggle grid snap (1 ft)",
            " H: Toggle this help",
            " Ctrl+Z: Undo",
            " Ctrl+Y: Redo",
        ]
        text_y = y + 60
        for text_str in help_texts:
            if text_str.endswith(":"):
                text = self.small_font.render(text_str, True, self.YELLOW)
            else:
                text = self.tiny_font.render(text_str, True, self.WHITE)
            app.screen.blit(text, (x + 30, text_y))
            text_y += 25