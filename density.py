"""
density.py - Traffic Density Calculation and Adaptive Green-Light Timing Module.
Provides classification into Low/Medium/High, UI color tokens, and adaptive timing formulas.
"""

# Color Palette for Density & UI
COLOR_LOW = (16, 185, 129)       # Emerald Green
COLOR_MEDIUM = (245, 158, 11)     # Amber / Orange
COLOR_HIGH = (239, 68, 68)       # Bright Crimson Red
COLOR_BG_CARD = (19, 28, 49)      # Dark Navy Slate
COLOR_BORDER = (30, 41, 59)       # Slate Border
COLOR_TEXT_PRIMARY = (255, 255, 255)
COLOR_TEXT_SECONDARY = (148, 163, 184)
COLOR_ACCENT_GREEN = (34, 197, 94)
COLOR_ACCENT_YELLOW = (234, 179, 8)
COLOR_ACCENT_RED = (239, 68, 68)

# Density Thresholds
THRESHOLD_LOW_MAX = 10
THRESHOLD_MED_MAX = 25

def get_density_level(count: int) -> str:
    """
    Classify vehicle count into Low, Medium, High density levels.
    
    0–10 vehicles: LOW
    11–25 vehicles: MEDIUM
    26+ vehicles: HIGH
    """
    if count <= THRESHOLD_LOW_MAX:
        return "Low"
    elif count <= THRESHOLD_MED_MAX:
        return "Medium"
    else:
        return "High"

def get_density_color(level_or_count) -> tuple[int, int, int]:
    """Return RGB color tuple corresponding to density level or count."""
    if isinstance(level_or_count, int):
        level = get_density_level(level_or_count)
    else:
        level = str(level_or_count).capitalize()

    if level == "Low":
        return COLOR_LOW
    elif level == "Medium":
        return COLOR_MEDIUM
    else:
        return COLOR_HIGH

def get_density_ratio(count: int, max_capacity: int = 45) -> float:
    """Return normalized fill ratio (0.0 to 1.0) for vertical meter rendering."""
    ratio = max(0.0, min(1.0, count / float(max_capacity)))
    return ratio

def calculate_adaptive_green_time(count: int) -> int:
    """
    Calculates adaptive green light duration based on vehicle count.
    
    0–10 vehicles:  15 seconds
    11–20 vehicles: 20 seconds
    21–30 vehicles: 30 seconds
    31–40 vehicles: 40 seconds
    41+ vehicles:   45 seconds
    """
    count = max(0, int(count))
    if count <= 10:
        return 15
    elif count <= 20:
        return 20
    elif count <= 30:
        return 30
    elif count <= 40:
        return 40
    else:
        return 45

if __name__ == "__main__":
    test_counts = [0, 5, 8, 12, 15, 20, 25, 30, 35, 40, 45, 55]
    print("--- Density & Green Time Calculation Verification ---")
    for c in test_counts:
        lvl = get_density_level(c)
        gt = calculate_adaptive_green_time(c)
        print(f"Vehicles: {c:2d} -> Level: {lvl:<6} | Green Duration: {gt:2d} seconds")
