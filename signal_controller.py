"""
signal_controller.py - State Machine for 4-Way Adaptive Traffic Signal Control.
Integrates Decision Tree ML model for real-time priority prediction and adaptive green timing.
"""

from ml_model import TrafficMLModel
from density import calculate_adaptive_green_time, get_density_level
from training_data import DIRECTION_NAMES

class SignalState:
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    ALL_RED = "ALL_RED"

class TrafficSignalController:
    def __init__(self, ml_model: TrafficMLModel):
        self.ml_model = ml_model
        
        # State tracking
        self.active_direction = "East"       # Initial active direction
        self.current_phase = SignalState.GREEN
        
        # Durations
        self.yellow_duration = 5.0           # Exactly 5.0 seconds Yellow warning phase
        self.all_red_duration = 1.0          # Clearance interval (sec)
        
        # Dynamic Green Time tracking
        self.allotted_green_time = 40.0
        self.time_remaining = 24.0           # Initial countdown matching reference UI
        
        # Waiting times tracking (for fair tie-breaking)
        self.waiting_times = {
            "North": 10.0,
            "South": 15.0,
            "East": 0.0,
            "West": 8.0
        }
        
        # Decision tracking
        self.next_phase_direction = "South"
        self.reason = "Highest Traffic (30 vehicles)"
        self.ai_input_snapshot = {"North": 12, "South": 5, "East": 30, "West": 8}
        self.ai_prediction = "East"
        self.ai_confidence = 100.0
        self.ai_details = {}
        
        # Signal heads status map
        self.signal_lights = {
            "North": SignalState.RED,
            "South": SignalState.RED,
            "East": SignalState.GREEN,
            "West": SignalState.RED
        }
        
        # History log for presentation analysis
        self.cycle_count = 0
        self.decision_history = []

    def get_signal_for(self, direction: str) -> str:
        """Returns GREEN, YELLOW, or RED for specified direction."""
        return self.signal_lights.get(direction, SignalState.RED)

    def update(self, dt: float, current_counts: dict[str, int]):
        """
        Update signal state machine timers and waiting durations.
        
        Args:
            dt: Delta time in seconds.
            current_counts: Dict of live vehicle counts {'North': N, 'South': S, 'East': E, 'West': W}
        """
        # 1. Update waiting times: increase for stopped directions, reset for active green direction
        for d in DIRECTION_NAMES:
            if d == self.active_direction and self.current_phase == SignalState.GREEN:
                self.waiting_times[d] = 0.0
            else:
                self.waiting_times[d] += dt

        # 2. Continuously run ML prediction preview for the "NEXT PHASE" & AI DECISION cards
        self._update_next_phase_preview(current_counts)
        
        # 3. Dynamic queue clearance: if active green queue is completely empty (count = 0)
        # and other directions have waiting vehicles, transition to yellow early
        if self.current_phase == SignalState.GREEN:
            active_queue = current_counts.get(self.active_direction, 0)
            other_queues = sum(current_counts[d] for d in DIRECTION_NAMES if d != self.active_direction)
            if active_queue == 0 and other_queues > 0 and self.time_remaining > 2.0:
                # Fast forward to end of green
                self.time_remaining = min(self.time_remaining, 1.0)

        # 4. Timer countdown
        self.time_remaining -= dt

        if self.current_phase == SignalState.GREEN:
            if self.time_remaining <= 0:
                # Switch to YELLOW phase for active direction
                self.current_phase = SignalState.YELLOW
                self.time_remaining = self.yellow_duration
                self.signal_lights[self.active_direction] = SignalState.YELLOW

        elif self.current_phase == SignalState.YELLOW:
            if self.time_remaining <= 0:
                # Switch to ALL-RED clearance interval
                self.current_phase = SignalState.ALL_RED
                self.time_remaining = self.all_red_duration
                for d in DIRECTION_NAMES:
                    self.signal_lights[d] = SignalState.RED

        elif self.current_phase == SignalState.ALL_RED:
            # Clearance interval finished: Run ML Decision Tree to pick next priority road
            if self.time_remaining <= 0:
                self._execute_ml_priority_transition(current_counts)

    def _update_next_phase_preview(self, current_counts: dict[str, int]):
        """Runs preview ML prediction on current live queue state for the user interface."""
        self.ai_input_snapshot = dict(current_counts)
        
        # If currently serving a road, evaluate which non-active road is highest
        # or evaluate overall maximum
        pred_dir, conf, reason, details = self.ml_model.predict_priority(current_counts, self.waiting_times)
        
        # For NEXT PHASE preview: if current road is still predicting highest because it hasn't cleared yet,
        # preview the highest waiting alternative road
        other_counts = {d: current_counts[d] for d in DIRECTION_NAMES if d != self.active_direction}
        if other_counts and sum(other_counts.values()) > 0:
            alt_dir, _, _, _ = self.ml_model.predict_priority(other_counts, self.waiting_times)
            self.next_phase_direction = alt_dir
        else:
            self.next_phase_direction = pred_dir

        self.ai_prediction = pred_dir
        self.ai_confidence = round(conf * 100.0, 1)
        self.ai_details = details

    def _execute_ml_priority_transition(self, current_counts: dict[str, int]):
        """
        Executes Scikit-Learn Decision Tree model to choose the next green direction
        based strictly on the CURRENT vehicle queue/density.
        """
        # 1. Take snapshot of live AI input features
        self.ai_input_snapshot = dict(current_counts)
        
        # 2. Invoke Decision Tree prediction with tie-breaking
        pred_dir, conf, reason, details = self.ml_model.predict_priority(self.ai_input_snapshot, self.waiting_times)
        
        # 3. If predicted road has 0 vehicles but other roads have traffic, pick the highest non-empty road
        if current_counts.get(pred_dir, 0) == 0:
            non_empty = {d: current_counts[d] for d in DIRECTION_NAMES if current_counts[d] > 0}
            if non_empty:
                pred_dir, conf, reason, details = self.ml_model.predict_priority(non_empty, self.waiting_times)
            else:
                # All queues empty: round robin
                curr_idx = DIRECTION_NAMES.index(self.active_direction)
                pred_dir = DIRECTION_NAMES[(curr_idx + 1) % 4]
                reason = "Routine Cycle (All Queues Empty)"

        self.ai_prediction = pred_dir
        self.ai_confidence = round(conf * 100.0, 1)
        self.ai_details = details
        self.active_direction = pred_dir
        self.reason = reason

        # 4. Calculate adaptive green time based on the selected road's CURRENT vehicle count
        target_count = current_counts.get(self.active_direction, 0)
        self.allotted_green_time = float(calculate_adaptive_green_time(target_count))
        self.time_remaining = self.allotted_green_time

        # 5. Reset waiting time for the selected green direction
        self.waiting_times[self.active_direction] = 0.0

        # 6. Set traffic lights: only selected direction gets GREEN, all others are RED
        for d in DIRECTION_NAMES:
            self.signal_lights[d] = SignalState.GREEN if d == self.active_direction else SignalState.RED

        self.current_phase = SignalState.GREEN
        self.cycle_count += 1
        
        # Log decision
        log_entry = {
            "cycle": self.cycle_count,
            "counts": self.ai_input_snapshot,
            "selected_dir": self.active_direction,
            "green_seconds": self.allotted_green_time,
            "reason": self.reason
        }
        self.decision_history.append(log_entry)
        print(f"[SignalController] Cycle #{self.cycle_count} | ML Predicted: {self.active_direction} ({target_count} veh) | Green Time: {int(self.allotted_green_time)}s | {self.reason}")

    def reset(self, initial_counts: dict[str, int]):
        """Reset signal controller to initial reference state."""
        self.active_direction = "East"
        self.current_phase = SignalState.GREEN
        self.allotted_green_time = 40.0
        self.time_remaining = 24.0
        self.next_phase_direction = "South"
        self.reason = "Highest Traffic (30 vehicles)"
        self.ai_input_snapshot = dict(initial_counts)
        self.ai_prediction = "East"
        self.ai_confidence = 100.0
        self.cycle_count = 0
        self.decision_history.clear()
        
        self.waiting_times = {
            "North": 10.0,
            "South": 15.0,
            "East": 0.0,
            "West": 8.0
        }
        
        for d in DIRECTION_NAMES:
            self.signal_lights[d] = SignalState.GREEN if d == "East" else SignalState.RED
