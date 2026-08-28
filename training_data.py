"""
training_data.py - Training dataset generator for AI-Based Adaptive Traffic Signal Simulation.
Generates comprehensive 4-way traffic count data mapped to the optimal priority direction.
"""

import numpy as np

# Direction mappings
DIRECTION_NAMES = ["North", "South", "East", "West"]
DIRECTION_TO_IDX = {"North": 0, "South": 1, "East": 2, "West": 3}
IDX_TO_DIRECTION = {0: "North", 1: "South", 2: "East", 3: "West"}

def get_training_dataset():
    """
    Generates training samples for Decision Tree Classifier.
    Features: [North_count, South_count, East_count, West_count]
    Target: 0 (North), 1 (South), 2 (East), 3 (West)
    """
    # 1. Base curated examples from project specifications
    curated_samples = [
        # [N, S, E, W], Priority Direction
        ([10, 5, 30, 8], "East"),
        ([25, 8, 12, 15], "North"),
        ([5, 20, 10, 15], "South"),
        ([8, 12, 10, 35], "West"),
        ([30, 15, 20, 10], "North"),
        ([5, 25, 40, 8], "East"),
        ([8, 10, 12, 30], "West"),
        ([10, 35, 15, 5], "South"),
        ([12, 5, 30, 8], "East"),   # Initial Reference State
        ([18, 10, 8, 25], "West"),
        ([4, 28, 14, 9], "South"),
        ([32, 11, 15, 18], "North"),
        ([15, 15, 35, 10], "East"),
        ([7, 6, 8, 29], "West"),
        ([2, 3, 4, 30], "West"),
        ([22, 6, 9, 11], "North"),
        ([3, 26, 8, 7], "South"),
        ([14, 12, 28, 10], "East"),
        ([40, 5, 10, 12], "North"),
        ([6, 38, 12, 15], "South"),
        ([31, 4, 45, 45], "East"),
        ([22, 15, 12, 10], "North"),
        ([8, 10, 12, 30], "West"),
    ]

    X = []
    y = []

    for counts, direction in curated_samples:
        X.append(counts)
        y.append(DIRECTION_TO_IDX[direction])

    # 2. Dense grid coverage to ensure Decision Tree accurately splits across all 4 features
    rng = np.random.default_rng(42)

    for _ in range(800):
        # Generate random vehicle counts (0 to 60)
        counts = rng.integers(0, 60, size=4).tolist()
        
        # Priority direction is strictly the road with maximum vehicle count
        max_idx = int(np.argmax(counts))
        X.append(counts)
        y.append(max_idx)

    # 3. Add single congested road edge cases
    for i in range(4):
        for heavy_traffic in [15, 20, 25, 30, 35, 40, 45, 50, 55]:
            for light_traffic in [0, 2, 5, 8, 10, 12]:
                counts = [light_traffic] * 4
                counts[i] = heavy_traffic
                X.append(counts)
                y.append(i)

    # 4. Add close contest edge cases
    for i in range(4):
        for other in range(4):
            if i != other:
                for base in [10, 20, 30, 40]:
                    counts = [5, 5, 5, 5]
                    counts[i] = base + 3
                    counts[other] = base
                    X.append(counts)
                    y.append(i)

    return np.array(X, dtype=np.int32), np.array(y, dtype=np.int32)
