"""
main.py - Main Entry Point for AI-Based Adaptive Traffic Signal Simulation.
Coordinates Pygame event loop, UI rendering, simulation physics, and ML decision integration.
"""

import sys
import os
import math
import time
import datetime

# Ensure window opens centered and visible on any monitor
os.environ["SDL_VIDEO_CENTERED"] = "1"

import pygame

# Initialize Pygame modules
pygame.init()
pygame.font.init()

from ml_model import TrafficMLModel
from density import (
    COLOR_LOW, COLOR_MEDIUM, COLOR_HIGH, COLOR_BG_CARD, COLOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT_GREEN,
    COLOR_ACCENT_YELLOW, COLOR_ACCENT_RED, get_density_level, get_density_color
)
from signal_controller import SignalState, TrafficSignalController
from traffic_simulation import TrafficSimulation
from ui_components import (
    THEME_BG, THEME_PANEL_BG, THEME_PANEL_BORDER, THEME_CARD_BG,
    THEME_CARD_BORDER, THEME_TEXT_WHITE, THEME_TEXT_MUTED, THEME_TEXT_DIM,
    UIHelper, UIButton, TrafficCardRenderer
)

# Window Configuration - 1280x720 (Fits cleanly on all standard screens and laptops)
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

class TrafficApp:
    def __init__(self):
        # Set window title and icon
        pygame.display.set_caption("AI-Based Adaptive Traffic Signal Simulation")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Load Fonts
        self.font_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_sub = pygame.font.SysFont("Segoe UI", 11)
        self.font_header = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.font_card_title = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.font_card_count = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_card_sub = pygame.font.SysFont("Segoe UI", 11)
        self.font_badge = pygame.font.SysFont("Segoe UI", 10, bold=True)
        self.font_timer = pygame.font.SysFont("Segoe UI", 28, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 12)
        self.font_body_bold = pygame.font.SysFont("Segoe UI", 12, bold=True)
        self.font_mono = pygame.font.SysFont("Consolas", 11)
        self.font_clock = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.font_btn = pygame.font.SysFont("Segoe UI", 11, bold=True)

        # 1. Initialize ML Model
        print("==================================================")
        print(" AI-BASED ADAPTIVE TRAFFIC SIGNAL SIMULATION")
        print(" College Engineering Project - Python & Pygame & Scikit-Learn")
        print("==================================================")
        self.ml_model = TrafficMLModel()

        # 2. Initialize Signal Controller & Simulation Engine
        self.controller = TrafficSignalController(self.ml_model)
        
        # Center simulation viewport dimensions
        self.sim_w = 666
        self.sim_h = 530
        self.simulation = TrafficSimulation(width=self.sim_w, height=self.sim_h)
        self.sim_surface = pygame.Surface((self.sim_w, self.sim_h))

        # Simulation execution state
        self.is_running = True
        self.is_paused = False

        # UI Layout Coordinates
        self.panel_left_rect = pygame.Rect(12, 58, 258, 592)
        self.panel_center_rect = pygame.Rect(278, 58, 686, 592)
        self.panel_right_rect = pygame.Rect(972, 58, 296, 592)
        self.panel_bottom_rect = pygame.Rect(12, 658, 1256, 52)

        # Buttons
        self._init_buttons()

    def _init_buttons(self):
        """Create UI buttons in bottom bar and side panels."""
        by = self.panel_bottom_rect.y + 10
        
        # Start / Pause / Reset buttons
        self.btn_start = UIButton(pygame.Rect(160, by, 76, 32), "▶ START", (22, 101, 52), (34, 197, 94), is_active=True)
        self.btn_pause = UIButton(pygame.Rect(244, by, 76, 32), "⏸ PAUSE", (30, 41, 59), (71, 85, 105))
        self.btn_reset = UIButton(pygame.Rect(328, by, 76, 32), "↺ RESET", (69, 26, 26), (220, 38, 38))

        # Traffic Mode Selector Buttons
        mx = 520
        self.btn_mode_low = UIButton(pygame.Rect(mx, by, 64, 32), "LOW", (30, 41, 59), (51, 65, 85), is_active=False)
        self.btn_mode_norm = UIButton(pygame.Rect(mx + 70, by, 72, 32), "NORMAL", (30, 41, 59), (51, 65, 85), is_active=True)
        self.btn_mode_high = UIButton(pygame.Rect(mx + 148, by, 64, 32), "HIGH", (30, 41, 59), (51, 65, 85), is_active=False)

        # Manual Inbound Vehicle Injection buttons (Left Panel bottom)
        iy = self.panel_left_rect.bottom - 42
        self.btn_add_n = UIButton(pygame.Rect(self.panel_left_rect.x + 12, iy, 52, 26), "+ N", (30, 41, 59), (51, 65, 85))
        self.btn_add_s = UIButton(pygame.Rect(self.panel_left_rect.x + 68, iy, 52, 26), "+ S", (30, 41, 59), (51, 65, 85))
        self.btn_add_e = UIButton(pygame.Rect(self.panel_left_rect.x + 124, iy, 52, 26), "+ E", (30, 41, 59), (51, 65, 85))
        self.btn_add_w = UIButton(pygame.Rect(self.panel_left_rect.x + 180, iy, 52, 26), "+ W", (30, 41, 59), (51, 65, 85))

    def handle_events(self):
        """Handle mouse clicks, keyboard shortcuts, and window close."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._toggle_pause()
                elif event.key == pygame.K_r:
                    self._reset_simulation()
                elif event.key == pygame.K_1:
                    self._set_traffic_mode("LOW")
                elif event.key == pygame.K_2:
                    self._set_traffic_mode("NORMAL")
                elif event.key == pygame.K_3:
                    self._set_traffic_mode("HIGH")
                elif event.key == pygame.K_n:
                    self.simulation.add_single_vehicle("North")
                elif event.key == pygame.K_s:
                    self.simulation.add_single_vehicle("South")
                elif event.key == pygame.K_e:
                    self.simulation.add_single_vehicle("East")
                elif event.key == pygame.K_w:
                    self.simulation.add_single_vehicle("West")

            # Button click handling
            if self.btn_start.handle_event(event):
                self._start_simulation()
            if self.btn_pause.handle_event(event):
                self._pause_simulation()
            if self.btn_reset.handle_event(event):
                self._reset_simulation()

            if self.btn_mode_low.handle_event(event):
                self._set_traffic_mode("LOW")
            if self.btn_mode_norm.handle_event(event):
                self._set_traffic_mode("NORMAL")
            if self.btn_mode_high.handle_event(event):
                self._set_traffic_mode("HIGH")

            if self.btn_add_n.handle_event(event):
                self.simulation.add_single_vehicle("North")
            if self.btn_add_s.handle_event(event):
                self.simulation.add_single_vehicle("South")
            if self.btn_add_e.handle_event(event):
                self.simulation.add_single_vehicle("East")
            if self.btn_add_w.handle_event(event):
                self.simulation.add_single_vehicle("West")

    def _start_simulation(self):
        self.is_paused = False
        self.btn_start.is_active = True
        self.btn_pause.is_active = False

    def _pause_simulation(self):
        self.is_paused = True
        self.btn_start.is_active = False
        self.btn_pause.is_active = True

    def _toggle_pause(self):
        if self.is_paused:
            self._start_simulation()
        else:
            self._pause_simulation()

    def _reset_simulation(self):
        self.simulation.reset_to_initial_state()
        initial_counts = self.simulation.get_inbound_counts()
        self.controller.reset(initial_counts)
        self.is_paused = False
        self.btn_start.is_active = True
        self.btn_pause.is_active = False
        print("[System] Simulation reset to initial reference state.")

    def _set_traffic_mode(self, mode: str):
        self.simulation.set_traffic_mode(mode)
        self.btn_mode_low.is_active = (mode == "LOW")
        self.btn_mode_norm.is_active = (mode == "NORMAL")
        self.btn_mode_high.is_active = (mode == "HIGH")

    def update(self, dt: float):
        """Update simulation and signal controller when not paused."""
        if not self.is_paused:
            # Query live vehicle counts
            counts = self.simulation.get_inbound_counts()
            
            # Update Signal State Machine and ML transitions
            self.controller.update(dt, counts)
            
            # Update Vehicle Movement & Dynamic Spawning
            self.simulation.update(dt, self.controller)

    def draw(self):
        """Render complete application frame matching reference UI."""
        # 1. Background Fill
        self.screen.fill(THEME_BG)

        # 2. Render Top Bar
        self._draw_top_bar()

        # 3. Render Left Panel (TRAFFIC STATUS)
        self._draw_left_panel()

        # 4. Render Center Panel (LIVE SIMULATION)
        self._draw_center_panel()

        # 5. Render Right Panel (CURRENT STATUS & AI DECISION)
        self._draw_right_panel()

        # 6. Render Bottom Bar
        self._draw_bottom_bar()

        # Flip screen buffer
        pygame.display.flip()

    def _draw_top_bar(self):
        """Draw dark title bar with application title and status badges."""
        bar_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 48)
        pygame.draw.rect(self.screen, (13, 19, 34), bar_rect)
        pygame.draw.line(self.screen, THEME_PANEL_BORDER, (0, 48), (WINDOW_WIDTH, 48), 1)

        # Title Text
        title_surf = self.font_title.render("AI-Based Adaptive Traffic Signal Simulation", True, THEME_TEXT_WHITE)
        self.screen.blit(title_surf, (16, 12))

        # Subtitle / Architecture chip
        sub_text = "College Engineering Project  |  Decision Tree ML Priority Engine  |  Real-Time Adaptive Timing"
        sub_surf = self.font_sub.render(sub_text, True, THEME_TEXT_MUTED)
        self.screen.blit(sub_surf, (title_surf.get_width() + 30, 16))

        # Right AI Engine Status Chip
        chip_rect = pygame.Rect(WINDOW_WIDTH - 220, 8, 206, 30)
        UIHelper.draw_rounded_rect(self.screen, (23, 33, 56), chip_rect, radius=15, border_color=(51, 65, 85), border_width=1)
        UIHelper.draw_glowing_circle(self.screen, (chip_rect.x + 14, chip_rect.centery), 4, COLOR_ACCENT_GREEN)
        ml_txt = self.font_badge.render("ML MODEL: TRAINED & ACTIVE", True, (226, 232, 240))
        self.screen.blit(ml_txt, (chip_rect.x + 24, chip_rect.centery - ml_txt.get_height() // 2))

    def _draw_left_panel(self):
        """Draw Left Panel: TRAFFIC STATUS with 4 directional cards."""
        UIHelper.draw_rounded_rect(self.screen, THEME_PANEL_BG, self.panel_left_rect, radius=8, border_color=THEME_PANEL_BORDER, border_width=1)

        # Header
        header_surf = self.font_header.render("TRAFFIC STATUS", True, (226, 232, 240))
        self.screen.blit(header_surf, (self.panel_left_rect.x + 14, self.panel_left_rect.y + 12))
        
        pygame.draw.line(self.screen, THEME_PANEL_BORDER, 
                         (self.panel_left_rect.x + 14, self.panel_left_rect.y + 36),
                         (self.panel_left_rect.right - 14, self.panel_left_rect.y + 36), 1)

        # Direction Cards
        counts = self.simulation.get_inbound_counts()
        card_w = self.panel_left_rect.width - 24
        card_h = 104
        start_y = self.panel_left_rect.y + 44
        gap_y = 8

        directions = ["North", "South", "East", "West"]
        for idx, direction in enumerate(directions):
            card_rect = pygame.Rect(self.panel_left_rect.x + 12, start_y + idx * (card_h + gap_y), card_w, card_h)
            count = counts.get(direction, 0)
            is_green = (self.controller.active_direction == direction and self.controller.current_phase == SignalState.GREEN)
            
            TrafficCardRenderer.draw_card(
                self.screen, card_rect, direction, count, is_green,
                self.font_card_title, self.font_card_count, self.font_card_sub, self.font_badge
            )

        # Inject Vehicle Prompt
        inject_lbl = self.font_sub.render("MANUAL VEHICLE INJECTION (DEMO):", True, THEME_TEXT_DIM)
        self.screen.blit(inject_lbl, (self.panel_left_rect.x + 12, self.panel_left_rect.bottom - 60))
        
        # Draw Add Buttons
        self.btn_add_n.draw(self.screen, self.font_btn)
        self.btn_add_s.draw(self.screen, self.font_btn)
        self.btn_add_e.draw(self.screen, self.font_btn)
        self.btn_add_w.draw(self.screen, self.font_btn)

    def _draw_center_panel(self):
        """Draw Center Panel: LIVE SIMULATION with 4-Way intersection canvas and live badges."""
        UIHelper.draw_rounded_rect(self.screen, THEME_PANEL_BG, self.panel_center_rect, radius=8, border_color=THEME_PANEL_BORDER, border_width=1)

        # Header Badge
        header_surf = self.font_header.render("LIVE TRAFFIC SIMULATION INTERSECTION", True, (226, 232, 240))
        self.screen.blit(header_surf, (self.panel_center_rect.x + 16, self.panel_center_rect.y + 12))

        # Live feed green dot
        pulse_color = COLOR_ACCENT_GREEN if not self.is_paused else COLOR_ACCENT_YELLOW
        UIHelper.draw_glowing_circle(self.screen, (self.panel_center_rect.right - 90, self.panel_center_rect.y + 18), 4, pulse_color)
        status_txt = "REAL-TIME" if not self.is_paused else "PAUSED"
        st_surf = self.font_badge.render(status_txt, True, pulse_color)
        self.screen.blit(st_surf, (self.panel_center_rect.right - 80, self.panel_center_rect.y + 12))

        # Render Simulation Surface
        sim_pos_x = self.panel_center_rect.x + 10
        sim_pos_y = self.panel_center_rect.y + 36
        self.simulation.draw(self.sim_surface, self.controller)
        self.screen.blit(self.sim_surface, (sim_pos_x, sim_pos_y))

        # Outline around simulation viewport
        pygame.draw.rect(self.screen, THEME_PANEL_BORDER, (sim_pos_x, sim_pos_y, self.sim_w, self.sim_h), width=1, border_radius=6)

    def _draw_right_panel(self):
        """Draw Right Panel: CURRENT STATUS, TIMERS, NEXT PHASE, SYSTEM MODE, and AI DECISION."""
        UIHelper.draw_rounded_rect(self.screen, THEME_PANEL_BG, self.panel_right_rect, radius=8, border_color=THEME_PANEL_BORDER, border_width=1)

        # Header
        header_surf = self.font_header.render("CURRENT STATUS", True, (226, 232, 240))
        self.screen.blit(header_surf, (self.panel_right_rect.x + 14, self.panel_right_rect.y + 12))

        pygame.draw.line(self.screen, THEME_PANEL_BORDER, 
                         (self.panel_right_rect.x + 14, self.panel_right_rect.y + 36),
                         (self.panel_right_rect.right - 14, self.panel_right_rect.y + 36), 1)

        rx = self.panel_right_rect.x + 14
        rw = self.panel_right_rect.width - 28
        curr_y = self.panel_right_rect.y + 44

        # ----------------------------------------------------
        # CARD 1: ACTIVE DIRECTION & REASON
        # ----------------------------------------------------
        c1_h = 68
        c1_rect = pygame.Rect(rx, curr_y, rw, c1_h)
        UIHelper.draw_rounded_rect(self.screen, THEME_CARD_BG, c1_rect, radius=6, border_color=THEME_CARD_BORDER, border_width=1)
        
        lbl_act = self.font_sub.render("Active Direction", True, THEME_TEXT_MUTED)
        self.screen.blit(lbl_act, (rx + 12, curr_y + 8))

        active_name = self.controller.active_direction
        phase_color = COLOR_ACCENT_GREEN if self.controller.current_phase == SignalState.GREEN else COLOR_ACCENT_YELLOW
        if self.controller.current_phase == SignalState.ALL_RED:
            phase_color = COLOR_ACCENT_RED
            
        act_surf = self.font_card_title.render(f"{active_name} Road", True, THEME_TEXT_WHITE)
        self.screen.blit(act_surf, (rx + 12, curr_y + 24))
        
        UIHelper.draw_glowing_circle(self.screen, (rx + rw - 18, curr_y + 22), 4, phase_color)

        reason_txt = f"Reason: {self.controller.reason}"
        if len(reason_txt) > 34:
            reason_txt = reason_txt[:32] + "..."
        lbl_rsn = self.font_sub.render(reason_txt, True, COLOR_ACCENT_GREEN)
        self.screen.blit(lbl_rsn, (rx + 12, curr_y + 46))

        curr_y += c1_h + 8

        # ----------------------------------------------------
        # CARD 2: GREEN LIGHT TIMER
        # ----------------------------------------------------
        c2_h = 86
        c2_rect = pygame.Rect(rx, curr_y, rw, c2_h)
        UIHelper.draw_rounded_rect(self.screen, THEME_CARD_BG, c2_rect, radius=6, border_color=THEME_CARD_BORDER, border_width=1)

        timer_lbl = self.font_sub.render("GREEN LIGHT TIMER", True, THEME_TEXT_MUTED)
        self.screen.blit(timer_lbl, (rx + 12, curr_y + 8))

        rem_sec = max(0, int(math.ceil(self.controller.time_remaining)))
        if self.controller.current_phase == SignalState.YELLOW:
            timer_digits = f"{rem_sec} sec (Yellow)"
            dig_color = COLOR_ACCENT_YELLOW
        elif self.controller.current_phase == SignalState.ALL_RED:
            timer_digits = f"Clearance"
            dig_color = COLOR_ACCENT_RED
        else:
            timer_digits = f"{rem_sec} sec"
            dig_color = COLOR_ACCENT_GREEN

        timer_surf = self.font_timer.render(timer_digits, True, dig_color)
        self.screen.blit(timer_surf, (rx + 12, curr_y + 24))

        total_time = max(1.0, float(self.controller.allotted_green_time))
        prog_ratio = max(0.0, min(1.0, self.controller.time_remaining / total_time))
        bar_w = rw - 24
        bar_h = 5
        bar_rect = pygame.Rect(rx + 12, curr_y + 66, bar_w, bar_h)
        UIHelper.draw_rounded_rect(self.screen, (15, 23, 42), bar_rect, radius=2)
        fill_w = max(3, int(bar_w * prog_ratio))
        UIHelper.draw_rounded_rect(self.screen, dig_color, pygame.Rect(rx + 12, curr_y + 66, fill_w, bar_h), radius=2)

        curr_y += c2_h + 8

        # ----------------------------------------------------
        # CARD 3: NEXT PHASE
        # ----------------------------------------------------
        c3_h = 58
        c3_rect = pygame.Rect(rx, curr_y, rw, c3_h)
        UIHelper.draw_rounded_rect(self.screen, THEME_CARD_BG, c3_rect, radius=6, border_color=THEME_CARD_BORDER, border_width=1)

        np_lbl = self.font_sub.render("NEXT PHASE", True, THEME_TEXT_MUTED)
        self.screen.blit(np_lbl, (rx + 12, curr_y + 8))

        next_dir = self.controller.next_phase_direction
        np_dir_surf = self.font_card_title.render(next_dir, True, (226, 232, 240))
        self.screen.blit(np_dir_surf, (rx + 12, curr_y + 26))

        starts_in_sec = max(1, rem_sec + int(self.controller.yellow_duration if self.controller.current_phase == SignalState.GREEN else 0))
        st_surf = self.font_sub.render(f"Starts in: {starts_in_sec} sec", True, THEME_TEXT_MUTED)
        self.screen.blit(st_surf, (rx + rw - st_surf.get_width() - 12, curr_y + 28))

        curr_y += c3_h + 8

        # ----------------------------------------------------
        # CARD 4: SYSTEM MODE
        # ----------------------------------------------------
        c4_h = 52
        c4_rect = pygame.Rect(rx, curr_y, rw, c4_h)
        UIHelper.draw_rounded_rect(self.screen, THEME_CARD_BG, c4_rect, radius=6, border_color=THEME_CARD_BORDER, border_width=1)

        mode_lbl = self.font_sub.render("SYSTEM MODE", True, THEME_TEXT_MUTED)
        self.screen.blit(mode_lbl, (rx + 12, curr_y + 6))

        mode_val = self.font_body_bold.render("Adaptive (AI)", True, COLOR_ACCENT_GREEN)
        self.screen.blit(mode_val, (rx + 12, curr_y + 24))

        sub_mode = self.font_sub.render("Learning & Adjusting", True, THEME_TEXT_MUTED)
        self.screen.blit(sub_mode, (rx + rw - sub_mode.get_width() - 12, curr_y + 26))

        curr_y += c4_h + 8

        # ----------------------------------------------------
        # CARD 5: AI DECISION DISPLAY (College Presentation Highlight)
        # ----------------------------------------------------
        c5_h = 224
        c5_rect = pygame.Rect(rx, curr_y, rw, c5_h)
        UIHelper.draw_rounded_rect(self.screen, (18, 28, 48), c5_rect, radius=6, border_color=(51, 65, 85), border_width=1)

        ai_header = self.font_header.render("AI DECISION DISPLAY", True, (56, 189, 248))
        self.screen.blit(ai_header, (rx + 12, curr_y + 10))

        # Model inputs snapshot
        inp_y = curr_y + 32
        self.screen.blit(self.font_badge.render("AI INPUT QUEUES:", True, THEME_TEXT_MUTED), (rx + 12, inp_y))
        
        inps = self.controller.ai_input_snapshot
        q_text1 = f"North: {inps.get('North', 0):2d}  |  South: {inps.get('South', 0):2d}"
        q_text2 = f"East:  {inps.get('East', 0):2d}  |  West:  {inps.get('West', 0):2d}"
        
        self.screen.blit(self.font_mono.render(q_text1, True, (241, 245, 249)), (rx + 12, inp_y + 16))
        self.screen.blit(self.font_mono.render(q_text2, True, (241, 245, 249)), (rx + 12, inp_y + 30))

        # Divider
        pygame.draw.line(self.screen, (40, 56, 84), (rx + 12, inp_y + 48), (rx + rw - 12, inp_y + 48), 1)

        # AI Prediction
        pred_y = inp_y + 54
        self.screen.blit(self.font_badge.render("AI PREDICTION:", True, THEME_TEXT_MUTED), (rx + 12, pred_y))
        pred_surf = self.font_card_title.render(f"{self.controller.ai_prediction} Road Priority", True, COLOR_ACCENT_GREEN)
        self.screen.blit(pred_surf, (rx + 12, pred_y + 15))

        # Reason
        rsn_y = pred_y + 36
        self.screen.blit(self.font_badge.render("REASON:", True, THEME_TEXT_MUTED), (rx + 12, rsn_y))
        rsn_str = self.controller.reason
        if len(rsn_str) > 30:
            rsn_str = rsn_str[:28] + "..."
        self.screen.blit(self.font_sub.render(rsn_str, True, (226, 232, 240)), (rx + 12, rsn_y + 15))

        # Green Time
        gt_y = rsn_y + 34
        self.screen.blit(self.font_badge.render("CALCULATED GREEN TIME:", True, THEME_TEXT_MUTED), (rx + 12, gt_y))
        gt_surf = self.font_body_bold.render(f"{int(self.controller.allotted_green_time)} sec (Adaptive)", True, COLOR_ACCENT_YELLOW)
        self.screen.blit(gt_surf, (rx + 12, gt_y + 15))

    def _draw_bottom_bar(self):
        """Draw Bottom Bar: Status, Start/Pause/Reset, Traffic Mode, Clock, Live Feed."""
        UIHelper.draw_rounded_rect(self.screen, THEME_PANEL_BG, self.panel_bottom_rect, radius=6, border_color=THEME_PANEL_BORDER, border_width=1)

        # Left Status Indicator
        status_dot_col = COLOR_ACCENT_GREEN if not self.is_paused else COLOR_ACCENT_YELLOW
        status_text = "System Active" if not self.is_paused else "System Paused"
        
        UIHelper.draw_glowing_circle(self.screen, (self.panel_bottom_rect.x + 20, self.panel_bottom_rect.centery), 4, status_dot_col)
        st_surf = self.font_body_bold.render(status_text, True, THEME_TEXT_WHITE)
        self.screen.blit(st_surf, (self.panel_bottom_rect.x + 32, self.panel_bottom_rect.centery - st_surf.get_height() // 2))

        # Draw Control Buttons
        self.btn_start.draw(self.screen, self.font_btn)
        self.btn_pause.draw(self.screen, self.font_btn)
        self.btn_reset.draw(self.screen, self.font_btn)

        # Traffic Mode Label & Buttons
        mode_lbl = self.font_badge.render("TRAFFIC RATE:", True, THEME_TEXT_MUTED)
        self.screen.blit(mode_lbl, (430, self.panel_bottom_rect.centery - mode_lbl.get_height() // 2))
        
        self.btn_mode_low.draw(self.screen, self.font_btn)
        self.btn_mode_norm.draw(self.screen, self.font_btn)
        self.btn_mode_high.draw(self.screen, self.font_btn)

        # Current Clock Time (Center-Right)
        now_str = datetime.datetime.now().strftime("%I:%M:%S %p")
        clock_surf = self.font_clock.render(now_str, True, (241, 245, 249))
        self.screen.blit(clock_surf, (self.panel_bottom_rect.right - 230, self.panel_bottom_rect.centery - clock_surf.get_height() // 2))

        # Right Live Feed indicator
        lf_dot_col = COLOR_ACCENT_GREEN if not self.is_paused else THEME_TEXT_DIM
        UIHelper.draw_glowing_circle(self.screen, (self.panel_bottom_rect.right - 105, self.panel_bottom_rect.centery), 4, lf_dot_col)
        lf_text = "↗ Live Feed" if not self.is_paused else "Paused"
        lf_surf = self.font_body_bold.render(lf_text, True, (226, 232, 240) if not self.is_paused else THEME_TEXT_DIM)
        self.screen.blit(lf_surf, (self.panel_bottom_rect.right - 94, self.panel_bottom_rect.centery - lf_surf.get_height() // 2))

    def run(self):
        """Main Pygame execution loop."""
        print("[System] Traffic Simulation Application Started. Running at 60 FPS.")
        
        last_time = time.perf_counter()
        while self.is_running:
            current_time = time.perf_counter()
            dt = current_time - last_time
            last_time = current_time
            
            # Cap dt to avoid physics spiral on lag
            dt = min(dt, 0.1)

            self.handle_events()
            self.update(dt)
            self.draw()

            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = TrafficApp()
    app.run()
