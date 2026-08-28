# AI-Based Adaptive Traffic Signal Simulation

An intelligent, real-time 4-way traffic intersection simulation and adaptive signal control system powered by **Python**, **Pygame**, and **Scikit-Learn Machine Learning (Decision Tree Classifier)**.

Designed and developed as a complete **College Engineering Project**.

---

## 🌟 Key Features

1. **Live 4-Way Intersection Simulation**:
   - High-fidelity visual intersection with asphalt roads, double-yellow divider lines, dashed lane markings, zebra pedestrian crossings, sidewalks, curbs, and corner landscaping.
   - Dynamic vehicle entities (**Sedans**, **SUVs**, **Motorcycles**, **Buses**) with individualized dimensions, speeds, colors, headlights, and brake lights.
   - Realistic multi-lane queueing with Intelligent Car-Following physics and safe braking deceleration curves.

2. **Machine Learning Priority Decision Engine**:
   - Utilizes `scikit-learn`'s `DecisionTreeClassifier` trained on 4-way traffic distribution patterns.
   - Live feature inputs: Approaching/waiting vehicle queues for $[N, S, E, W]$.
   - Real-time priority inference, confidence scoring, and contextual rationale generation.

3. **Traffic Density Estimation**:
   - **LOW (0–10 vehicles)**: Color-coded Green, nominal traffic flow.
   - **MEDIUM (11–25 vehicles)**: Color-coded Amber/Orange, moderate queue accumulation.
   - **HIGH (26+ vehicles)**: Color-coded Crimson Red, severe congestion requiring immediate clearance.

4. **Dynamic Adaptive Green Light Timing**:
   - Computes dynamic phase durations tailored to the queue length:
     - **Low**: $15 - 20\text{ seconds}$
     - **Medium**: $20 - 30\text{ seconds}$
     - **High**: $30 - 45\text{ seconds}$

5. **Complete Signal State Machine**:
   - Strict non-conflicting phase cycling: $\text{GREEN} \rightarrow \text{YELLOW (5s)} \rightarrow \text{ALL-RED (1s clearance)} \rightarrow \text{ML Priority Prediction} \rightarrow \text{Next GREEN}$.

6. **Interactive Engineering Dashboard**:
   - **Left Panel (TRAFFIC STATUS)**: Real-time direction cards with live counts, density badges, and vertical density gauges.
   - **Center Panel (SIMULATION VIEWPORT)**: Real-time 60 FPS graphical rendering of the intersection, moving vehicles, and 3-bulb LED traffic lights.
   - **Right Panel (CURRENT STATUS & AI DECISION)**: Active direction, Reason, Green countdown timer, Next phase preview, and AI Decision Matrix.
   - **Bottom Bar**: System status pill, live digital clock, Live Feed status, Start/Pause/Reset controls, and Traffic Arrival Rate selectors.

---

## 📁 Project Architecture

```
d:/traffic simulation/
│
├── main.py                  # Main Pygame application entry point and dashboard loop
├── ml_model.py              # Scikit-learn DecisionTreeClassifier training & inference
├── training_data.py         # Multi-scenario 4-way traffic training dataset generator
├── signal_controller.py     # Adaptive signal state machine & phase transition logic
├── traffic_simulation.py    # 4-way intersection layout, multi-lane queues & vehicle spawners
├── vehicle.py               # Vehicle physics, car-following model & sprite rendering
├── density.py               # Density thresholds, color tokens & adaptive timing formulas
├── ui_components.py         # Custom UI buttons, density meters & styled cards
├── test_simulation.py       # Automated headless sanity and verification test suite
└── README.md                # Project documentation and presentation guide
```

---

## 🚀 How to Run the Project

### Prerequisites

Ensure you have Python 3.10+ installed.

Install the required libraries:
```bash
pip install pygame scikit-learn numpy
```

### Launching the Simulation

Run the application:
```bash
python main.py
```

### Running Automated Test Suite

To verify all ML algorithms, density calculations, and simulation mechanics:
```bash
python test_simulation.py
```

---

## 🎮 Interactive Controls & Keyboard Shortcuts

| Control | Shortcut Key | Description |
| :--- | :---: | :--- |
| **Start Simulation** | `[SPACE]` or Click `[▶ START]` | Resumes vehicle movement, timers, and AI adaptation. |
| **Pause Simulation** | `[SPACE]` or Click `[⏸ PAUSE]` | Freezes simulation physics and countdown timers. |
| **Reset to Initial State** | `[R]` or Click `[↺ RESET]` | Restores reference queues ($N=12, S=5, E=30, W=8$). |
| **Traffic Mode: Low** | `[1]` or Click `[LOW]` | Spawns arriving vehicles at a relaxed rate (~5s interval). |
| **Traffic Mode: Normal** | `[2]` or Click `[NORMAL]` | Standard vehicle arrival rate (~3s interval). |
| **Traffic Mode: High** | `[3]` or Click `[HIGH]` | Congestion stress-test arrival rate (~1.5s interval). |
| **Manual Vehicle Injection** | `[N]`, `[S]`, `[E]`, `[W]` | Spawns an instant vehicle into North, South, East, or West road. |

---

## 🔬 Mathematical Formulations

### 1. Density Classification Function

$$\text{Density}(C) = \begin{cases} \text{LOW} & \text{if } 0 \le C \le 10 \\ \text{MEDIUM} & \text{if } 11 \le C \le 25 \\ \text{HIGH} & \text{if } C \ge 26 \end{cases}$$

### 2. Adaptive Green Time Calculation

$$T_{\text{green}}(C) = \begin{cases} 
15 + \left(\frac{C}{10}\right) \times 5 & \text{if } C \le 10 \\
20 + \left(\frac{C - 10}{15}\right) \times 10 & \text{if } 10 < C \le 25 \\
\min\left(45,\, 30 + \left(\frac{C - 25}{10}\right) \times 10\right) & \text{if } C > 25
\end{cases}$$

---

## 🎓 College Presentation Walkthrough

When presenting this project to evaluators:

1. **Initial Condition Alignment**:
   - Point out that the initial queues ($N=12, S=5, E=30, W=8$) trigger the **Decision Tree ML model** to select **East** as priority.
   - East receives an adaptive green light duration of **$40\text{ seconds}$** due to high density ($30$ vehicles).
2. **Live Depletion & Adaptation**:
   - As East vehicles cross the intersection, East vehicle count decreases in real-time.
   - Arriving vehicles increase counts on North, South, and West.
   - When East timer expires (transitioning Green $\rightarrow$ Yellow $\rightarrow$ Clearance), the **Decision Tree re-evaluates the live queues** and automatically switches priority to the next congested direction (e.g., North or West).
3. **Interactive Demonstration**:
   - Click `[+ N]` or press `[N]` repeatedly during the presentation to create a sudden traffic surge on North.
   - Watch the AI Decision Matrix detect the queue surge and award the subsequent Green phase to North!
