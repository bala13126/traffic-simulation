"""
vehicle.py - Vehicle entity, physics simulation, queuing behavior, and detailed visual rendering.
Supports multiple vehicle types (Cars, Motorcycles, Buses) with dynamic headlights, brake lights,
and smooth car-following mechanics.
"""

import math
import random
import pygame

# Vehicle Color Palette
VEHICLE_COLORS = [
    (220, 38, 38),    # Ruby Red
    (37, 99, 235),    # Royal Blue
    (241, 245, 249),  # Pearl White
    (71, 85, 105),    # Slate Charcoal
    (234, 88, 12),    # Sunset Orange
    (13, 148, 136),   # Teal Green
    (202, 138, 4),    # Golden Yellow
    (168, 85, 247),   # Purple
    (15, 118, 110),   # Deep Emerald
    (203, 213, 225),  # Silver
]

class VehicleType:
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    BUS = "bus"

VEHICLE_SPECS = {
    VehicleType.MOTORCYCLE: {"length": 18, "width": 8, "max_speed": 3.6, "accel": 0.22, "decel": 0.35, "weight": 1},
    VehicleType.CAR:        {"length": 28, "width": 15, "max_speed": 3.2, "accel": 0.18, "decel": 0.30, "weight": 1},
    VehicleType.BUS:        {"length": 44, "width": 18, "max_speed": 2.6, "accel": 0.12, "decel": 0.25, "weight": 2}
}

class Vehicle:
    def __init__(self, vehicle_id: int, direction: str, lane: int, x: float, y: float, vtype: str = None):
        self.id = vehicle_id
        self.direction = direction  # "North", "South", "East", "West"
        self.lane = lane            # 0 (outer), 1 (inner)
        self.x = float(x)
        self.y = float(y)
        
        # Vehicle category
        if vtype is None:
            r = random.random()
            if r < 0.15:
                self.vtype = VehicleType.MOTORCYCLE
            elif r < 0.85:
                self.vtype = VehicleType.CAR
            else:
                self.vtype = VehicleType.BUS
        else:
            self.vtype = vtype

        spec = VEHICLE_SPECS[self.vtype]
        self.length = spec["length"]
        self.width = spec["width"]
        self.max_speed = spec["max_speed"] + random.uniform(-0.15, 0.15)
        self.accel = spec["accel"]
        self.decel = spec["decel"]
        
        self.speed = 0.0
        self.color = random.choice(VEHICLE_COLORS)
        
        # State tracking
        self.is_braking = False
        self.is_stopped = False
        self.has_crossed_stopline = False
        self.is_departed = False

    def get_bounding_box(self) -> pygame.Rect:
        """Get approximate bounding box for collision detection."""
        if self.direction in ["North", "South"]:
            return pygame.Rect(int(self.x - self.width / 2), int(self.y - self.length / 2), self.width, self.length)
        else:
            return pygame.Rect(int(self.x - self.length / 2), int(self.y - self.width / 2), self.length, self.width)

    def update(self, lead_vehicle, stopline_coord: float, signal_state: str, intersection_center: tuple[float, float]):
        """
        Update vehicle position and speed using car-following logic and stopline compliance.
        """
        cx, cy = intersection_center
        target_speed = self.max_speed
        self.is_braking = False

        # 1. Check stop line distance
        dist_to_stop = float("inf")
        if self.direction == "North":
            if not self.has_crossed_stopline:
                dist_to_stop = stopline_coord - (self.y + self.length / 2)
                if dist_to_stop <= 0:
                    self.has_crossed_stopline = True
        elif self.direction == "South":
            if not self.has_crossed_stopline:
                dist_to_stop = (self.y - self.length / 2) - stopline_coord
                if dist_to_stop <= 0:
                    self.has_crossed_stopline = True
        elif self.direction == "East":
            if not self.has_crossed_stopline:
                dist_to_stop = (self.x - self.length / 2) - stopline_coord
                if dist_to_stop <= 0:
                    self.has_crossed_stopline = True
        elif self.direction == "West":
            if not self.has_crossed_stopline:
                dist_to_stop = stopline_coord - (self.x + self.length / 2)
                if dist_to_stop <= 0:
                    self.has_crossed_stopline = True

        # 2. Stop Line Compliance (only before crossing)
        if not self.has_crossed_stopline:
            if signal_state in ["RED", "YELLOW"]:
                can_clear = (signal_state == "YELLOW" and dist_to_stop < 20 and self.speed > 1.5)
                if not can_clear:
                    if dist_to_stop < 90:
                        desired_dist = max(0.0, dist_to_stop - 4.0)
                        if desired_dist < 3.0:
                            target_speed = 0.0
                        else:
                            target_speed = min(target_speed, (desired_dist / 50.0) * self.max_speed)
                        self.is_braking = True

        # 3. Leading Vehicle Car-Following (maintain safe bumper gap)
        if lead_vehicle is not None:
            dist_to_lead = float("inf")
            if self.direction == "North":
                dist_to_lead = (lead_vehicle.y - lead_vehicle.length / 2) - (self.y + self.length / 2)
            elif self.direction == "South":
                dist_to_lead = (self.y - self.length / 2) - (lead_vehicle.y + lead_vehicle.length / 2)
            elif self.direction == "East":
                dist_to_lead = (self.x - self.length / 2) - (lead_vehicle.x + lead_vehicle.length / 2)
            elif self.direction == "West":
                dist_to_lead = (lead_vehicle.x - lead_vehicle.length / 2) - (self.x + self.length / 2)

            min_gap = 6.0
            slowdown_range = 40.0 + self.speed * 6.0

            if dist_to_lead < min_gap + 2.0:
                target_speed = 0.0
                self.is_braking = True
            elif dist_to_lead < slowdown_range:
                gap_ratio = max(0.0, (dist_to_lead - min_gap) / (slowdown_range - min_gap))
                target_speed = min(target_speed, lead_vehicle.speed * 0.9 + gap_ratio * self.max_speed * 0.6)
                self.is_braking = True

        # 4. Accelerate / Decelerate
        if self.speed < target_speed:
            self.speed = min(target_speed, self.speed + self.accel)
        elif self.speed > target_speed:
            self.speed = max(target_speed, self.speed - self.decel)

        if self.speed < 0.05:
            self.speed = 0.0
            self.is_stopped = True
        else:
            self.is_stopped = False

        # 5. Position Update
        if self.direction == "North":
            self.y += self.speed
        elif self.direction == "South":
            self.y -= self.speed
        elif self.direction == "East":
            self.x -= self.speed
        elif self.direction == "West":
            self.x += self.speed

    def draw(self, surface: pygame.Surface):
        """Render realistic vehicle sprite with roof, windshields, headlights and taillights."""
        if self.direction == "North":
            w, h = self.width, self.length
        elif self.direction == "South":
            w, h = self.width, self.length
        elif self.direction == "East":
            w, h = self.length, self.width
        elif self.direction == "West":
            w, h = self.length, self.width

        veh_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Shadow
        shadow_rect = pygame.Rect(1, 2, w - 2, h - 2)
        pygame.draw.rect(veh_surf, (0, 0, 0, 80), shadow_rect, border_radius=3)

        # Body
        body_rect = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(veh_surf, self.color, body_rect, border_radius=3)
        
        # Outline
        border_color = (max(0, self.color[0] - 40), max(0, self.color[1] - 40), max(0, self.color[2] - 40))
        pygame.draw.rect(veh_surf, border_color, body_rect, width=1, border_radius=3)

        # Glass & Roof Styling
        glass_color = (30, 41, 59, 230)
        roof_color = (max(0, self.color[0] - 20), max(0, self.color[1] - 20), max(0, self.color[2] - 20))

        if self.vtype == VehicleType.CAR:
            if self.direction in ["North", "South"]:
                front_y = 3 if self.direction == "North" else h - 7
                rear_y = h - 7 if self.direction == "North" else 3
                pygame.draw.rect(veh_surf, glass_color, (2, front_y, w - 4, 4), border_radius=1)
                pygame.draw.rect(veh_surf, glass_color, (2, rear_y, w - 4, 3), border_radius=1)
                pygame.draw.rect(veh_surf, roof_color, (2, 8, w - 4, h - 16), border_radius=2)
            else:
                front_x = 3 if self.direction == "East" else w - 7
                rear_x = w - 7 if self.direction == "East" else 3
                pygame.draw.rect(veh_surf, glass_color, (front_x, 2, 4, h - 4), border_radius=1)
                pygame.draw.rect(veh_surf, glass_color, (rear_x, 2, 3, h - 4), border_radius=1)
                pygame.draw.rect(veh_surf, roof_color, (8, 2, w - 16, h - 4), border_radius=2)

        elif self.vtype == VehicleType.BUS:
            if self.direction in ["North", "South"]:
                for wy in range(6, h - 8, 6):
                    pygame.draw.rect(veh_surf, glass_color, (1, wy, 2, 4))
                    pygame.draw.rect(veh_surf, glass_color, (w - 3, wy, 2, 4))
                pygame.draw.rect(veh_surf, glass_color, (2, 2 if self.direction == "North" else h - 6, w - 4, 4))
            else:
                for wx in range(6, w - 8, 6):
                    pygame.draw.rect(veh_surf, glass_color, (wx, 1, 4, 2))
                    pygame.draw.rect(veh_surf, glass_color, (wx, h - 3, 4, 2))
                pygame.draw.rect(veh_surf, glass_color, (2 if self.direction == "East" else w - 6, 2, 4, h - 4))

        elif self.vtype == VehicleType.MOTORCYCLE:
            pygame.draw.circle(veh_surf, (254, 240, 138), (w // 2, h // 2), 3)

        # Headlights & Taillights
        headlight_col = (254, 240, 138)
        brake_col = (255, 40, 40) if self.is_braking or self.is_stopped else (160, 20, 20)

        if self.direction == "North":
            pygame.draw.circle(veh_surf, headlight_col, (2, h - 1), 2)
            pygame.draw.circle(veh_surf, headlight_col, (w - 3, h - 1), 2)
            pygame.draw.rect(veh_surf, brake_col, (1, 0, 3, 2))
            pygame.draw.rect(veh_surf, brake_col, (w - 4, 0, 3, 2))
        elif self.direction == "South":
            pygame.draw.circle(veh_surf, headlight_col, (2, 1), 2)
            pygame.draw.circle(veh_surf, headlight_col, (w - 3, 1), 2)
            pygame.draw.rect(veh_surf, brake_col, (1, h - 2, 3, 2))
            pygame.draw.rect(veh_surf, brake_col, (w - 4, h - 2, 3, 2))
        elif self.direction == "East":
            pygame.draw.circle(veh_surf, headlight_col, (1, 2), 2)
            pygame.draw.circle(veh_surf, headlight_col, (1, h - 3), 2)
            pygame.draw.rect(veh_surf, brake_col, (w - 2, 1, 2, 3))
            pygame.draw.rect(veh_surf, brake_col, (w - 2, h - 4, 2, 3))
        elif self.direction == "West":
            pygame.draw.circle(veh_surf, headlight_col, (w - 1, 2), 2)
            pygame.draw.circle(veh_surf, headlight_col, (w - 1, h - 3), 2)
            pygame.draw.rect(veh_surf, brake_col, (0, 1, 2, 3))
            pygame.draw.rect(veh_surf, brake_col, (0, h - 4, 2, 3))

        dest_rect = veh_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(veh_surf, dest_rect)
