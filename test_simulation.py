"""
test_simulation.py - Automated verification and sanity test suite for the Traffic Simulation.
Runs headless simulation cycles, tests ML model predictions, state machine transitions,
and dynamic green light duration calculations.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy" # Headless mode for automated tests

import pygame
pygame.init()

from ml_model import TrafficMLModel
from density import get_density_level, calculate_adaptive_green_time, THRESHOLD_LOW_MAX, THRESHOLD_MED_MAX
from signal_controller import SignalState, TrafficSignalController
from traffic_simulation import TrafficSimulation
from training_data import DIRECTION_NAMES

def test_ml_model():
    print("Testing ML Model & Dynamic Priority Prediction...")
    ml = TrafficMLModel()
    assert ml.is_trained, "ML Model should be trained."
    
    # 1. Standard priority test cases
    test_cases = [
        ({"North": 12, "South": 5, "East": 30, "West": 8}, None, "East"),
        ({"North": 18, "South": 10, "East": 8, "West": 25}, None, "West"),
        ({"North": 22, "South": 15, "East": 12, "West": 10}, None, "North"),
        ({"North": 5, "South": 28, "East": 10, "West": 15}, None, "South"),
    ]
    for counts, wt, expected_dir in test_cases:
        pred_dir, conf, reason, _ = ml.predict_priority(counts, wt)
        print(f"  Input: {counts} -> Prediction: {pred_dir} (Expected: {expected_dir}) | Reason: {reason}")
        assert pred_dir == expected_dir, f"Expected {expected_dir}, got {pred_dir}"

    # 2. Tie-Breaking Test Case: East=45, West=45 (prefer road with longer waiting time)
    tie_counts = {"North": 31, "South": 4, "East": 45, "West": 45}
    wt_east_older = {"North": 5.0, "South": 10.0, "East": 40.0, "West": 20.0}
    wt_west_older = {"North": 5.0, "South": 10.0, "East": 15.0, "West": 50.0}
    
    p_east, _, r_east, _ = ml.predict_priority(tie_counts, wt_east_older)
    print(f"  Tie Case (East waited 40s vs West 20s) -> Prediction: {p_east} | Reason: {r_east}")
    assert p_east == "East", f"Expected East on tie break, got {p_east}"

    p_west, _, r_west, _ = ml.predict_priority(tie_counts, wt_west_older)
    print(f"  Tie Case (West waited 50s vs East 15s) -> Prediction: {p_west} | Reason: {r_west}")
    assert p_west == "West", f"Expected West on tie break, got {p_west}"

    print("[OK] ML Model & Tie-Breaking tests passed successfully.\n")

def test_density_calculations():
    print("Testing Density & Adaptive Timing...")
    assert get_density_level(5) == "Low"
    assert get_density_level(10) == "Low"
    assert get_density_level(11) == "Medium"
    assert get_density_level(25) == "Medium"
    assert get_density_level(26) == "High"
    assert get_density_level(45) == "High"

    t5 = calculate_adaptive_green_time(5)
    t15 = calculate_adaptive_green_time(15)
    t25 = calculate_adaptive_green_time(25)
    t35 = calculate_adaptive_green_time(35)
    t45 = calculate_adaptive_green_time(45)

    print(f"  5 vehicles -> {t5}s (Expected: 15s)")
    print(f"  15 vehicles -> {t15}s (Expected: 20s)")
    print(f"  25 vehicles -> {t25}s (Expected: 30s)")
    print(f"  35 vehicles -> {t35}s (Expected: 40s)")
    print(f"  45 vehicles -> {t45}s (Expected: 45s)")

    assert t5 == 15, f"t5 expected 15, got {t5}"
    assert t15 == 20, f"t15 expected 20, got {t15}"
    assert t25 == 30, f"t25 expected 30, got {t25}"
    assert t35 == 40, f"t35 expected 40, got {t35}"
    assert t45 == 45, f"t45 expected 45, got {t45}"
    print("[OK] Density & Timing tests passed successfully.\n")

def test_simulation_lifecycle():
    print("Testing Simulation & Dynamic Adaptive Transition Lifecycle...")
    ml = TrafficMLModel()
    controller = TrafficSignalController(ml)
    sim = TrafficSimulation(666, 530)
    
    # Verify initial reference condition
    counts = sim.get_inbound_counts()
    print(f"  Initial counts: {counts}")
    assert counts["East"] == 30, f"Initial East count should be 30, got {counts['East']}"
    assert counts["North"] == 12, f"Initial North count should be 12, got {counts['North']}"
    assert counts["South"] == 5, f"Initial South count should be 5, got {counts['South']}"
    assert counts["West"] == 8, f"Initial West count should be 8, got {counts['West']}"

    assert controller.active_direction == "East"
    assert controller.get_signal_for("East") == SignalState.GREEN
    assert controller.get_signal_for("North") == SignalState.RED
    assert controller.get_signal_for("South") == SignalState.RED
    assert controller.get_signal_for("West") == SignalState.RED
    assert controller.yellow_duration == 5.0, f"Expected 5.0s yellow duration, got {controller.yellow_duration}"

    # Run simulation for 200 virtual ticks
    dt = 0.05
    for step in range(300):
        c = sim.get_inbound_counts()
        controller.update(dt, c)
        sim.update(dt, controller)

    print(f"  Counts after 15s simulation: {sim.get_inbound_counts()}")
    print(f"  Active Direction: {controller.active_direction} | Phase: {controller.current_phase}")
    print("[OK] Simulation lifecycle test passed successfully.\n")

def test_surface_rendering():
    print("Testing Pygame Canvas & Full UI Rendering...")
    ml = TrafficMLModel()
    controller = TrafficSignalController(ml)
    sim = TrafficSimulation(666, 530)
    
    surf = pygame.Surface((666, 530))
    sim.draw(surf, controller)

    from main import TrafficApp
    app = TrafficApp()
    app.update(0.05)
    app.draw()
    print("[OK] Canvas and Full UI draw completed without errors.\n")

if __name__ == "__main__":
    print("==========================================")
    print("RUNNING TRAFFIC SIMULATION SANITY TESTS")
    print("==========================================\n")
    test_ml_model()
    test_density_calculations()
    test_simulation_lifecycle()
    test_surface_rendering()
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
