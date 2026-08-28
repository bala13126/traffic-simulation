"""
ui_components.py - Custom UI Widgets and Design Tokens for Pygame.
Provides rounded containers, buttons, density meters, digital timers, and glowing status pills.
"""

import pygame
import math
from density import (
    COLOR_LOW, COLOR_MEDIUM, COLOR_HIGH, COLOR_BG_CARD, COLOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT_GREEN,
    get_density_level, get_density_color, get_density_ratio
)

# Dark Navy Theme Colors
THEME_BG = (10, 15, 29)          # Main Deep Dark Navy Background
THEME_PANEL_BG = (15, 23, 42)    # Dark Slate Panel Background
THEME_PANEL_BORDER = (30, 41, 59)# Panel Border
THEME_CARD_BG = (23, 33, 56)     # Inner Card Background
THEME_CARD_BORDER = (40, 56, 84) # Inner Card Border
THEME_TEXT_WHITE = (255, 255, 255)
THEME_TEXT_MUTED = (148, 163, 184)
THEME_TEXT_DIM = (100, 116, 139)

class UIHelper:
    @staticmethod
    def draw_rounded_rect(surface: pygame.Surface, color: tuple, rect: pygame.Rect, radius: int = 8, border_color: tuple = None, border_width: int = 1):
        """Draw filled rounded rectangle with optional border."""
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border_color and border_width > 0:
            pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=radius)

    @staticmethod
    def draw_glowing_circle(surface: pygame.Surface, center: tuple[int, int], radius: int, color: tuple):
        """Draw circle with soft transparent bloom ring."""
        # Outer glow
        glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        glow_color = (color[0], color[1], color[2], 60)
        pygame.draw.circle(glow_surf, glow_color, (radius * 2, radius * 2), radius + 4)
        surface.blit(glow_surf, (center[0] - radius * 2, center[1] - radius * 2))
        
        # Solid center
        pygame.draw.circle(surface, color, center, radius)

class UIButton:
    def __init__(self, rect: pygame.Rect, text: str, bg_color: tuple, hover_color: tuple, text_color: tuple = THEME_TEXT_WHITE, is_active: bool = False):
        self.rect = rect
        self.text = text
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_active = is_active
        self.is_hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if button was clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        color = self.hover_color if (self.is_hovered or self.is_active) else self.bg_color
        border_col = (255, 255, 255) if self.is_active else THEME_PANEL_BORDER
        border_w = 2 if self.is_active else 1
        
        UIHelper.draw_rounded_rect(surface, color, self.rect, radius=6, border_color=border_col, border_width=border_w)
        
        txt_surf = font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

class TrafficCardRenderer:
    """Renders Left Panel direction card: direction, count, level, and vertical density bar."""
    
    @staticmethod
    def draw_card(surface: pygame.Surface, rect: pygame.Rect, direction: str, count: int, 
                  is_green: bool, font_title: pygame.font.Font, font_count: pygame.font.Font, 
                  font_sub: pygame.font.Font, font_badge: pygame.font.Font):
        
        # Background & Highlight if signal is GREEN
        bg_col = (28, 42, 70) if is_green else THEME_CARD_BG
        border_col = (34, 197, 94) if is_green else THEME_CARD_BORDER
        border_w = 2 if is_green else 1
        
        UIHelper.draw_rounded_rect(surface, bg_col, rect, radius=8, border_color=border_col, border_width=border_w)
        
        # 1. Direction Name (e.g. "NORTH")
        dir_text = direction.upper()
        dir_surf = font_title.render(dir_text, True, (226, 232, 240))
        surface.blit(dir_surf, (rect.x + 14, rect.y + 12))
        
        # Active Green Indicator Dot if green
        if is_green:
            UIHelper.draw_glowing_circle(surface, (rect.x + 14 + dir_surf.get_width() + 12, rect.y + 19), 4, COLOR_ACCENT_GREEN)

        # 2. Big Vehicle Count & "vehicles" label
        count_str = str(count)
        count_surf = font_count.render(count_str, True, THEME_TEXT_WHITE)
        surface.blit(count_surf, (rect.x + 14, rect.y + 36))
        
        veh_lbl_surf = font_sub.render("vehicles", True, THEME_TEXT_MUTED)
        surface.blit(veh_lbl_surf, (rect.x + 14 + count_surf.get_width() + 6, rect.y + 54))

        # 3. Traffic Level Badge (Low / Medium / High)
        density_level = get_density_level(count)
        density_col = get_density_color(density_level)
        
        # Pill badge
        badge_w = 70
        badge_h = 22
        badge_rect = pygame.Rect(rect.x + 14, rect.y + 82, badge_w, badge_h)
        badge_bg = (density_col[0] // 5, density_col[1] // 5, density_col[2] // 5)
        UIHelper.draw_rounded_rect(surface, badge_bg, badge_rect, radius=11, border_color=density_col, border_width=1)
        
        badge_txt = font_badge.render(density_level, True, density_col)
        surface.blit(badge_txt, badge_txt.get_rect(center=badge_rect.center))

        # 4. Vertical Density Bar Indicator (Right side of the card)
        meter_x = rect.right - 22
        meter_y = rect.y + 14
        meter_w = 8
        meter_h = rect.height - 28
        meter_rect = pygame.Rect(meter_x, meter_y, meter_w, meter_h)
        
        # Meter Background track
        UIHelper.draw_rounded_rect(surface, (15, 23, 42), meter_rect, radius=4, border_color=THEME_PANEL_BORDER, border_width=1)
        
        # Meter Fill Level (Bottom to Top)
        ratio = get_density_ratio(count, max_capacity=35)
        fill_h = max(4, int(meter_h * ratio))
        fill_y = meter_y + meter_h - fill_h
        fill_rect = pygame.Rect(meter_x, fill_y, meter_w, fill_h)
        
        UIHelper.draw_rounded_rect(surface, density_col, fill_rect, radius=4)
