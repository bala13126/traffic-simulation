"""
ml_model.py - Scikit-learn Decision Tree Machine Learning Model for Traffic Signal Priority.
Trains a DecisionTreeClassifier on 4-way traffic count features and predicts the optimal priority road.
"""

import numpy as np
from sklearn.tree import DecisionTreeClassifier
from training_data import get_training_dataset, DIRECTION_NAMES, DIRECTION_TO_IDX, IDX_TO_DIRECTION

class TrafficMLModel:
    def __init__(self, max_depth=10, random_state=42):
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = DecisionTreeClassifier(
            criterion="gini",
            max_depth=self.max_depth,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=self.random_state
        )
        self.is_trained = False
        self.train()

    def train(self):
        """Train the Decision Tree model using the generated dataset."""
        X, y = get_training_dataset()
        self.model.fit(X, y)
        self.is_trained = True
        train_acc = self.model.score(X, y) * 100.0
        print(f"[ML Model] DecisionTreeClassifier initialized & trained successfully.")
        print(f"[ML Model] Training samples: {len(X)} | Training Accuracy: {train_acc:.1f}% | Tree Depth: {self.model.get_depth()}")

    def predict_priority(self, counts: dict, waiting_times: dict = None) -> tuple[str, float, str, dict]:
        """
        Predict priority direction based on 4-way vehicle counts and fair tie-breaking rules.
        
        Args:
            counts: dict with keys "North", "South", "East", "West" and integer values.
            waiting_times: optional dict of waiting durations in seconds for tie resolution.
            
        Returns:
            predicted_direction: str ("North", "South", "East", or "West")
            confidence: float (0.0 to 1.0)
            reason: str human-readable explanation
            debug_info: dict with probabilities and feature values
        """
        n_c = int(counts.get("North", 0))
        s_c = int(counts.get("South", 0))
        e_c = int(counts.get("East", 0))
        w_c = int(counts.get("West", 0))
        
        features = np.array([[n_c, s_c, e_c, w_c]], dtype=np.int32)

        # 1. Check for ties among maximum counts
        max_count = max(n_c, s_c, e_c, w_c)
        tied_dirs = [d for d in DIRECTION_NAMES if counts.get(d, 0) == max_count]

        if len(tied_dirs) > 1 and max_count > 0:
            # Fair Tie-Breaking Rule: Choose the road that has waited the longest
            if waiting_times is not None:
                # Find tied road with maximum accumulated wait time
                best_dir = max(tied_dirs, key=lambda d: waiting_times.get(d, 0.0))
                wait_sec = int(round(waiting_times.get(best_dir, 0.0)))
                reason = f"High Traffic ({max_count} vehicles) - Tie Break by Waiting Time ({wait_sec}s)"
            else:
                best_dir = tied_dirs[0]
                reason = f"High Traffic ({max_count} vehicles) - Equal Priority Queue"

            predicted_dir = best_dir
            confidence = 1.0
            probabilities = {d: (1.0 if d == predicted_dir else 0.0) for d in DIRECTION_NAMES}

        else:
            # 2. Decision Tree Prediction
            pred_idx = int(self.model.predict(features)[0])
            prob_vector = self.model.predict_proba(features)[0]
            
            probabilities = {dir_name: 0.0 for dir_name in DIRECTION_NAMES}
            for class_idx, prob in enumerate(prob_vector):
                actual_class = self.model.classes_[class_idx]
                probabilities[IDX_TO_DIRECTION[actual_class]] = float(prob)

            predicted_dir = IDX_TO_DIRECTION[pred_idx]
            
            # Double check: ensure predicted direction has the maximum count
            if counts.get(predicted_dir, 0) < max_count:
                # Fallback to direct argmax if tree boundary had an edge
                predicted_dir = max(counts, key=counts.get)

            confidence = float(probabilities.get(predicted_dir, 1.0))
            pred_count = counts.get(predicted_dir, 0)

            # Generate contextual rationale
            if pred_count >= 26:
                reason = f"Highest Traffic ({pred_count} vehicles) - High Density Priority"
            elif pred_count >= 11:
                reason = f"Highest Traffic ({pred_count} vehicles) - Medium Queue Priority"
            elif pred_count > 0:
                reason = f"Highest Traffic ({pred_count} vehicles) - Low Queue Clearance"
            else:
                reason = "Routine Cycle Allotment (All Queues Empty)"

        debug_info = {
            "inputs": counts,
            "probabilities": probabilities,
            "confidence_pct": round(confidence * 100, 1),
            "tree_depth": self.model.get_depth(),
            "n_leaves": self.model.get_n_leaves(),
            "features": ["North", "South", "East", "West"]
        }

        return predicted_dir, confidence, reason, debug_info

if __name__ == "__main__":
    ml = TrafficMLModel()
    test_cases = [
        ({"North": 12, "South": 5, "East": 30, "West": 8}, None),
        ({"North": 31, "South": 4, "East": 45, "West": 45}, {"North": 10.0, "South": 5.0, "East": 30.0, "West": 15.0}),
        ({"North": 18, "South": 10, "East": 8, "West": 25}, None),
        ({"North": 22, "South": 15, "East": 12, "West": 10}, None)
    ]
    for tc, wt in test_cases:
        p_dir, conf, rsn, _ = ml.predict_priority(tc, wt)
        print(f"Counts: {tc} -> Prediction: {p_dir} | Conf: {conf*100:.1f}% | Reason: {rsn}")
