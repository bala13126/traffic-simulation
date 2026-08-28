"""
traffic_simulation.py - 4-Way Intersection Physics and Vehicle Spawner Engine.
Renders road geometry, crosswalks, sidewalks, traffic lights, and manages multi-lane vehicle queues.
"""

import math
import random
import pygame
from vehicle import Vehicle, VehicleType
from signal_controller import SignalState, TrafficSignalController
from density import COLOR_LOW, COLOR_MEDIUM, COLOR_HIGH

# Visual Road Constants
COLOR_GRASS = (22, 101, 52)         # Deep Forest Green
COLOR_GRASS_ACCENT = (21, 128, 61)  # Grass highlight
COLOR_SIDEWALK = (51, 65, 85)       # Slate Sidewalk
COLOR_CURB = (100, 116, 139)        # Curb border
COLOR_ASPHALT = (15, 23, 42)        # Very Dark Slate Asphalt
COLOR_ROAD_MARKING = (248, 250, 252)# Bright White Markings
COLOR_YELLOW_LINE = (234, 179, 8)   # Solid Yellow Centerline

class TrafficSimulation:
    def __init__(self, width: int = 666, height: int = 530):
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        
        # Road Dimensions
        self.road_width = 136          # Total road width
        self.half_road = self.road_width // 2
        self.lane_width = 31           # Width of single lane
        self.stopline_dist = 80        # Distance from center to stop line
        
        # Vehicles storage per direction
        self.vehicles = {
            "North": [],
            "South": [],
            "East": [],
            "West": []
        }
        self.vehicle_id_counter = 0
        
        # Traffic Spawning Rates (seconds per vehicle per direction)
        self.traffic_mode = "NORMAL"   # "LOW", "NORMAL", "HIGH"
        self.spawn_intervals = {
            "LOW": {"min": 4.5, "max": 7.5},
            "NORMAL": {"min": 2.2, "max": 4.5},
            "HIGH": {"min": 1.0, "max": 2.2}
        }
        self.spawn_timers = {
            "North": 2.0,
            "South": 3.5,
            "East": 1.0,
            "West": 2.5
        }
        
        # Road Inbound Coordinates (Multi-lane alignment)
        self.lane_coords = {
            "North": {
                0: self.center_x + self.lane_width // 2 + 4,
                1: self.center_x + self.lane_width + self.lane_width // 2 + 2
            },
            "South": {
                0: self.center_x - self.lane_width // 2 - 4,
                1: self.center_x - self.lane_width - self.lane_width // 2 - 2
            },
            "East": {
                0: self.center_y - self.lane_width // 2 - 4,
                1: self.center_y - self.lane_width - self.lane_width // 2 - 2
            },
            "West": {
                0: self.center_y + self.lane_width // 2 + 4,
                1: self.center_y + self.lane_width + self.lane_width // 2 + 2
            }
        }
        
        # Stop line coordinates for each direction
        self.stoplines = {
            "North": self.center_y - self.stopline_dist,
            "South": self.center_y + self.stopline_dist,
            "East": self.center_x + self.stopline_dist,
            "West": self.center_x - self.stopline_dist
        }
        
        # Traffic Light Head Positions
        self.signal_head_positions = {
            "North": (self.center_x + self.half_road + 12, self.center_y - self.stopline_dist - 12),
            "South": (self.center_x - self.half_road - 36, self.center_y + self.stopline_dist + 12),
            "East":  (self.center_x + self.stopline_dist + 12, self.center_y - self.half_road - 36),
            "West":  (self.center_x - self.stopline_dist - 12, self.center_y + self.half_road + 12)
        }
        
        # Pre-render decorative corner trees
        self._generate_decorations()
        
        # Initialize standard initial state
        self.reset_to_initial_state()

    def _generate_decorations(self):
        """Generate static tree coordinates for natural scenery."""
        random.seed(1337)
        self.trees = []
        corner_bounds = [
            (20, self.center_x - self.half_road - 25, 20, self.center_y - self.half_road - 25),
            (self.center_x + self.half_road + 25, self.width - 20, 20, self.center_y - self.half_road - 25),
            (20, self.center_x - self.half_road - 25, self.center_y + self.half_road + 25, self.height - 20),
            (self.center_x + self.half_road + 25, self.width - 20, self.center_y + self.half_road + 25, self.height - 20)
        ]
        for xmin, xmax, ymin, ymax in corner_bounds:
            for _ in range(5):
                tx = random.randint(xmin, xmax)
                ty = random.randint(ymin, ymax)
                radius = random.randint(8, 14)
                shade = random.choice([(16, 185, 129), (5, 150, 105), (4, 120, 87)])
                self.trees.append((tx, ty, radius, shade))
        random.seed()

    def set_traffic_mode(self, mode: str):
        """Set traffic arrival intensity: LOW, NORMAL, HIGH."""
        if mode in self.spawn_intervals:
            self.traffic_mode = mode
            print(f"[Simulation] Traffic Mode switched to {mode}")

    def reset_to_initial_state(self):
        """
        Populate the simulation with the exact reference condition:
        North = 12 vehicles (Medium)
        South = 5 vehicles (Low)
        East = 30 vehicles (High)
        West = 8 vehicles (Low)
        """
        for d in self.vehicles:
            self.vehicles[d].clear()
            
        self.vehicle_id_counter = 0

        target_counts = {
            "North": 12,
            "South": 5,
            "East": 30,
            "West": 8
        }

        for direction, count in target_counts.items():
            self._spawn_queue(direction, count)

    def _spawn_queue(self, direction: str, count: int):
        """Spawn initial queued vehicles lined up before the stopline."""
        for i in range(count):
            self.vehicle_id_counter += 1
            lane = i % 2  # Distribute across 2 inbound lanes
            rank = i // 2 # Position in lane
            
            veh_len = 28
            gap = 6
            offset = 8 + rank * (veh_len + gap)
            
            if direction == "North":
                x = self.lane_coords["North"][lane]
                y = self.stoplines["North"] - offset
                v = Vehicle(self.vehicle_id_counter, "North", lane, x, y)
            elif direction == "South":
                x = self.lane_coords["South"][lane]
                y = self.stoplines["South"] + offset
                v = Vehicle(self.vehicle_id_counter, "South", lane, x, y)
            elif direction == "East":
                x = self.stoplines["East"] + offset
                y = self.lane_coords["East"][lane]
                v = Vehicle(self.vehicle_id_counter, "East", lane, x, y)
            elif direction == "West":
                x = self.stoplines["West"] - offset
                y = self.lane_coords["West"][lane]
                v = Vehicle(self.vehicle_id_counter, "West", lane, x, y)
                
            self.vehicles[direction].append(v)

    def add_single_vehicle(self, direction: str):
        """Spawn a new arriving vehicle at the approach edge."""
        self.vehicle_id_counter += 1
        
        # Pick least crowded lane
        lane0_vehs = [v for v in self.vehicles[direction] if v.lane == 0 and not v.has_crossed_stopline]
        lane1_vehs = [v for v in self.vehicles[direction] if v.lane == 1 and not v.has_crossed_stopline]
        lane = 0 if len(lane0_vehs) <= len(lane1_vehs) else 1
        chosen_lane_vehs = lane0_vehs if lane == 0 else lane1_vehs

        # Calculate spawn coordinate behind the rearmost car in this lane
        veh_len = 28
        gap = 8

        if direction == "North":
            x = self.lane_coords["North"][lane]
            if chosen_lane_vehs:
                rearmost_y = min(v.y for v in chosen_lane_vehs)
                y = min(-20.0, rearmost_y - veh_len - gap)
            else:
                y = self.stoplines["North"] - 15.0
            v = Vehicle(self.vehicle_id_counter, "North", lane, x, y)

        elif direction == "South":
            x = self.lane_coords["South"][lane]
            if chosen_lane_vehs:
                rearmost_y = max(v.y for v in chosen_lane_vehs)
                y = max(self.height + 20.0, rearmost_y + veh_len + gap)
            else:
                y = self.stoplines["South"] + 15.0
            v = Vehicle(self.vehicle_id_counter, "South", lane, x, y)

        elif direction == "East":
            y = self.lane_coords["East"][lane]
            if chosen_lane_vehs:
                rearmost_x = max(v.x for v in chosen_lane_vehs)
                x = max(self.width + 20.0, rearmost_x + veh_len + gap)
            else:
                x = self.stoplines["East"] + 15.0
            v = Vehicle(self.vehicle_id_counter, "East", lane, x, y)

        elif direction == "West":
            y = self.lane_coords["West"][lane]
            if chosen_lane_vehs:
                rearmost_x = min(v.x for v in chosen_lane_vehs)
                x = min(-20.0, rearmost_x - veh_len - gap)
            else:
                x = self.stoplines["West"] - 15.0
            v = Vehicle(self.vehicle_id_counter, "West", lane, x, y)

        self.vehicles[direction].append(v)

    def get_inbound_counts(self) -> dict[str, int]:
        """
        Count approaching and queued vehicles in each direction.
        As soon as a vehicle crosses the stop line into the intersection,
        it has left the approach queue and count decrements immediately!
        """
        counts = {}
        for d in ["North", "South", "East", "West"]:
            c = sum(1 for v in self.vehicles[d] if not v.has_crossed_stopline)
            counts[d] = max(0, c)
        return counts

    def update(self, dt: float, controller: TrafficSignalController):
        """Update simulation physics, dynamic spawning, and vehicle departures."""
        # 1. Spawners
        limits = self.spawn_intervals[self.traffic_mode]
        for d in ["North", "South", "East", "West"]:
            self.spawn_timers[d] -= dt
            if self.spawn_timers[d] <= 0:
                current_inbound = self.get_inbound_counts()[d]
                if current_inbound < 50:
                    self.add_single_vehicle(d)
                self.spawn_timers[d] = random.uniform(limits["min"], limits["max"])

        # 2. Update each direction's vehicles with car-following
        for d in ["North", "South", "East", "West"]:
            sig_state = controller.get_signal_for(d)
            stopline_pos = self.stoplines[d]
            
            # Separate by lane
            for lane_idx in [0, 1]:
                lane_vehs = [v for v in self.vehicles[d] if v.lane == lane_idx]
                
                # Sort vehicles by progression towards intersection
                if d == "North":
                    lane_vehs.sort(key=lambda v: v.y, reverse=True)
                elif d == "South":
                    lane_vehs.sort(key=lambda v: v.y, reverse=False)
                elif d == "East":
                    lane_vehs.sort(key=lambda v: v.x, reverse=False)
                elif d == "West":
                    lane_vehs.sort(key=lambda v: v.x, reverse=True)

                for i, veh in enumerate(lane_vehs):
                    lead = lane_vehs[i - 1] if i > 0 else None
                    veh.update(lead, stopline_pos, sig_state, (self.center_x, self.center_y))

            # 3. Clean up departed vehicles
            remaining = []
            for v in self.vehicles[d]:
                out_of_bounds = False
                if d == "North" and v.y > self.height + 60:
                    out_of_bounds = True
                elif d == "South" and v.y < -60:
                    out_of_bounds = True
                elif d == "East" and v.x < -60:
                    out_of_bounds = True
                elif d == "West" and v.x > self.width + 60:
                    out_of_bounds = True
                    
                if not out_of_bounds:
                    remaining.append(v)
            self.vehicles[d] = remaining

    def draw(self, surface: pygame.Surface, controller: TrafficSignalController):
        """Render the complete 4-way intersection simulation canvas."""
        # 1. Background Grass & Sidewalks
        surface.fill(COLOR_GRASS)
        pygame.draw.rect(surface, COLOR_GRASS_ACCENT, (0, 0, self.width, self.height), width=3)

        # Trees
        for tx, ty, r, shade in self.trees:
            pygame.draw.circle(surface, (0, 0, 0, 40), (tx + 2, ty + 2), r)
            pygame.draw.circle(surface, shade, (tx, ty), r)
            pygame.draw.circle(surface, (shade[0] + 20, shade[1] + 20, shade[2] + 20), (tx - 2, ty - 2), r // 2)

        # 2. Sidewalk Base
        sw_pad = 14
        pygame.draw.rect(surface, COLOR_SIDEWALK, 
                         (self.center_x - self.half_road - sw_pad, 0, self.road_width + sw_pad * 2, self.height))
        pygame.draw.rect(surface, COLOR_SIDEWALK, 
                         (0, self.center_y - self.half_road - sw_pad, self.width, self.road_width + sw_pad * 2))
        
        # Curbs
        pygame.draw.rect(surface, COLOR_CURB,
                         (self.center_x - self.half_road - sw_pad, 0, self.road_width + sw_pad * 2, self.height), width=2)
        pygame.draw.rect(surface, COLOR_CURB,
                         (0, self.center_y - self.half_road - sw_pad, self.width, self.road_width + sw_pad * 2), width=2)

        # 3. Asphalt Roads
        pygame.draw.rect(surface, COLOR_ASPHALT, 
                         (self.center_x - self.half_road, 0, self.road_width, self.height))
        pygame.draw.rect(surface, COLOR_ASPHALT, 
                         (0, self.center_y - self.half_road, self.width, self.road_width))

        # 4. Road Markings & Zebra Crossings
        self._draw_road_markings(surface)

        # 5. Render Vehicles
        for d in ["North", "South", "East", "West"]:
            for v in self.vehicles[d]:
                v.draw(surface)

        # 6. Render Traffic Signal Posts
        self._draw_traffic_lights(surface, controller)

    def _draw_road_markings(self, surface: pygame.Surface):
        """Draw lane lines, stop lines, zebra crossings, and directional indicators."""
        y_offset = 3
        # Vertical Yellow Centerline
        pygame.draw.line(surface, COLOR_YELLOW_LINE, (self.center_x - y_offset, 0), 
                         (self.center_x - y_offset, self.center_y - self.stopline_dist), 2)
        pygame.draw.line(surface, COLOR_YELLOW_LINE, (self.center_x + y_offset, 0), 
                         (self.center_x + y_offset, self.center_y - self.stopline_dist), 2)
        pygame.draw.line(surface, COLOR_YELLOW_LINE, (self.center_x - y_offset, self.center_y + self.stopline_dist), 
                         (self.center_x - y_offset, self.height), 2)
        pygame.draw.line(surface, COLOR_YELLOW_LINE, (self.center_x + y_offset, self.center_y + self.stopline_dist), 
                         (self.center_x + y_offset, self.height), 2)

        # Horizontal Yellow Centerline
        pygame.draw.line(surface, COLOR_YELLOW_LINE, (0, self.center_y - y_offset), 
                         (self.center_x - self.stopline_dist, self.center_y - y_offset), 2)
        pygame.draw.line(surface, COLOR_YELLOW_LINE, (0, self.center_y + y_offset), 
                         (self.center_x - self.stopline_dist, self.center_y + y_offset), 2)
        pygame.draw.line(surface, COLOR_YELLOW_LINE, (self.center_x + self.stopline_dist, self.center_y - y_offset), 
                         (self.width, self.center_y - y_offset), 2)
        pygame.draw.line(surface, COLOR_YELLOW_LINE, (self.center_x + self.stopline_dist, self.center_y + y_offset), 
                         (self.width, self.center_y + y_offset), 2)

        # Dashed White Lane Dividers
        dash_len = 12
        dash_space = 8
        nx = self.center_x + self.lane_width
        for y in range(0, self.center_y - self.stopline_dist, dash_len + dash_space):
            pygame.draw.line(surface, COLOR_ROAD_MARKING, (nx, y), (nx, min(self.center_y - self.stopline_dist, y + dash_len)), 2)
        
        sx = self.center_x - self.lane_width
        for y in range(self.center_y + self.stopline_dist, self.height, dash_len + dash_space):
            pygame.draw.line(surface, COLOR_ROAD_MARKING, (sx, y), (sx, min(self.height, y + dash_len)), 2)

        ey = self.center_y - self.lane_width
        for x in range(self.center_x + self.stopline_dist, self.width, dash_len + dash_space):
            pygame.draw.line(surface, COLOR_ROAD_MARKING, (x, ey), (min(self.width, x + dash_len), ey), 2)

        wy = self.center_y + self.lane_width
        for x in range(0, self.center_x - self.stopline_dist, dash_len + dash_space):
            pygame.draw.line(surface, COLOR_ROAD_MARKING, (x, wy), (min(self.center_x - self.stopline_dist, x + dash_len), wy), 2)

        # Solid Stop Lines
        pygame.draw.line(surface, COLOR_ROAD_MARKING, 
                         (self.center_x, self.center_y - self.stopline_dist), 
                         (self.center_x + self.half_road, self.center_y - self.stopline_dist), 4)
        pygame.draw.line(surface, COLOR_ROAD_MARKING, 
                         (self.center_x - self.half_road, self.center_y + self.stopline_dist), 
                         (self.center_x, self.center_y + self.stopline_dist), 4)
        pygame.draw.line(surface, COLOR_ROAD_MARKING, 
                         (self.center_x + self.stopline_dist, self.center_y - self.half_road), 
                         (self.center_x + self.stopline_dist, self.center_y), 4)
        pygame.draw.line(surface, COLOR_ROAD_MARKING, 
                         (self.center_x - self.stopline_dist, self.center_y), 
                         (self.center_x - self.stopline_dist, self.center_y + self.half_road), 4)

        # Zebra Crosswalks
        self._draw_zebra_crosswalks(surface)

        # Direction Labels on Roads
        font = pygame.font.SysFont("Segoe UI", 12, bold=True)
        lbl_n = font.render("NORTH", True, (148, 163, 184))
        lbl_s = font.render("SOUTH", True, (148, 163, 184))
        lbl_e = font.render("EAST", True, (148, 163, 184))
        lbl_w = font.render("WEST", True, (148, 163, 184))

        surface.blit(lbl_n, (self.center_x + 8, 12))
        surface.blit(lbl_s, (self.center_x - 50, self.height - 26))
        surface.blit(lbl_e, (self.width - 42, self.center_y - 22))
        surface.blit(lbl_w, (12, self.center_y + 10))

    def _draw_zebra_crosswalks(self, surface: pygame.Surface):
        """Draw pedestrian zebra crossings before intersection entry."""
        z_w = 5
        z_gap = 5
        for x in range(self.center_x - self.half_road + 2, self.center_x + self.half_road - 2, z_w + z_gap):
            pygame.draw.rect(surface, (230, 235, 245, 180), (x, self.center_y - self.stopline_dist + 4, z_w, 12))
            pygame.draw.rect(surface, (230, 235, 245, 180), (x, self.center_y + self.stopline_dist - 16, z_w, 12))

        for y in range(self.center_y - self.half_road + 2, self.center_y + self.half_road - 2, z_w + z_gap):
            pygame.draw.rect(surface, (230, 235, 245, 180), (self.center_x + self.stopline_dist - 16, y, 12, z_w))
            pygame.draw.rect(surface, (230, 235, 245, 180), (self.center_x - self.stopline_dist + 4, y, 12, z_w))

    def _draw_traffic_lights(self, surface: pygame.Surface, controller: TrafficSignalController):
        """Draw physical 3-bulb traffic lights with bloom glow effect."""
        for direction, (hx, hy) in self.signal_head_positions.items():
            state = controller.get_signal_for(direction)
            
            housing_w = 24
            housing_h = 56
            housing_rect = pygame.Rect(hx - housing_w // 2, hy - housing_h // 2, housing_w, housing_h)
            
            pygame.draw.rect(surface, (15, 23, 42), housing_rect, border_radius=4)
            pygame.draw.rect(surface, (71, 85, 105), housing_rect, width=1, border_radius=4)
            
            r_center = (hx, hy - 16)
            y_center = (hx, hy)
            g_center = (hx, hy + 16)
            radius = 5

            # Red Bulb
            if state in [SignalState.RED, SignalState.ALL_RED]:
                pygame.draw.circle(surface, (239, 68, 68, 80), r_center, radius + 3)
                pygame.draw.circle(surface, (239, 68, 68), r_center, radius)
                pygame.draw.circle(surface, (254, 202, 202), r_center, 2)
            else:
                pygame.draw.circle(surface, (69, 26, 26), r_center, radius)

            # Yellow Bulb
            if state == SignalState.YELLOW:
                pygame.draw.circle(surface, (234, 179, 8, 80), y_center, radius + 3)
                pygame.draw.circle(surface, (234, 179, 8), y_center, radius)
                pygame.draw.circle(surface, (254, 240, 138), y_center, 2)
            else:
                pygame.draw.circle(surface, (66, 52, 18), y_center, radius)

            # Green Bulb
            if state == SignalState.GREEN:
                pygame.draw.circle(surface, (34, 197, 94, 80), g_center, radius + 3)
                pygame.draw.circle(surface, (34, 197, 94), g_center, radius)
                pygame.draw.circle(surface, (187, 247, 208), g_center, 2)
            else:
                pygame.draw.circle(surface, (20, 60, 35), g_center, radius)
