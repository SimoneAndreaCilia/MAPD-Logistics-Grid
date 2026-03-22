# MAPD Logistics Grid: Multi-Agent System for Object Recovery

## Project Overview
The **MAPD Logistics Grid** is a Multi-Agent System (MAS) simulation designed to coordinate a fleet of autonomous agents tasked with locating and recovering objects scattered across a logistics environment. The agents must explore the grid, detect hidden objects, and transport them to designated warehouses.

<p align="center">
  <img src="data/A.png" alt="MAPD Logistics Grid 25x25" width="325">
</p>

While the map structure (walls, corridors, and warehouses) is known initially, the specific locations of the objects are hidden. Agents must use their sensors to "discover" these items through active exploration.

### Core Objectives (Goals)
The system aims to optimize three key performance indicators:
1) **Success Rate**: Maximize the number of objects successfully detected and delivered.
2) **Time Efficiency**: Minimize the total time (ticks) required for the recovery operation.
3) **Energy Efficiency**: Minimize the average energy consumption across the agent fleet.

---

## Environment Characteristics
The simulation takes place on a 2D grid composed of several cell types:
*   **Transit Zones**: Open corridors and yards for movement.
*   **Warehouses**: Specific zones for delivery, featuring dedicated **Entry** and **Exit** points.
*   **Obstacles**: Static walls and shelves that block movement and vision.
*   **Objects**: Target items located at specific coordinates (Ground Truth).

Obstacles and warehouses are static. Agents lack global knowledge of object positions and must rely on their local perception.

---

## Agent Specifications
Each agent starts at the top-left coordinate `[0,0]` and is equipped with:
*   **Position Tracking**: Current grid coordinates.
*   **Visibility Sensors**: 
    *   Configurable perception range (Manhattan distance).
    *   Obstacle and object detection.
    *   Line-of-Sight (LoS) logic: Vision is occluded by walls.
    *   Warehouse entrance/exit recognition.
*   **Energy Management**: Limited battery (typically 500 units). Every move costs 1 unit.
*   **Local Memory**: A persistent map built by the agent as it explores the grid.
*   **Communication Sensor**: Detects nearby agents to share information.
*   **Decision-Making Engine**: Autonomous strategy selection (e.g., Frontier-based exploration vs. pathfinding to known targets).

*Note: In this implementation, agent overlapping is permitted to simplify the coordination logic.*

---

## Roles & Strategies
Each agent is assigned a **Role** (defining their mission) and a **Strategy** (defining how they move).

### Agent Roles
*   **Scout**: Specializes in rapid exploration. It seeks unknown areas and, upon discovering objects, attempts to rendezvous with Collectors or Coordinators to share their findings.
*   **Collector**: The "workhorse" of the fleet. Its primary goal is to travel to known object locations, pick them up, and deliver them to the nearest warehouse entrance.
*   **Coordinator**: Acts as a static communication relay. It navigates to a strategically calculated central position and enters a "stasis" mode to facilitate map and objective sharing between mobile agents.

### Movement Strategies
*   **Frontier**: Standard exploration that targets "frontier" cells (the boundary between explored and unknown space).
*   **WallFollower**: An exploration pattern that prioritizes staying adjacent to walls, effective for mapping long corridors and room perimeters.
*   **Spiral**: Moves in an expanding geometric spiral from its starting point to systematically cover the local area.
*   **Greedy**: Always targets the nearest known objective (like the closest frontier) using the most direct path.
*   **RandomTarget**: A stochastic strategy that picks exploration targets with a degree of randomness, occasionally actively seeking out other agents to exchange information.


---

## Communication Logic
Agents share knowledge through an intersection of their communication ranges. When two or more agents are close enough:
1) They **merge their local maps**, filling in each other's "blind spots."
2) They **exchange known object locations**, allowing an agent to head towards a target discovered by another.

---

## Simulation Mechanics
*   **Tick System**: The simulation time advances by +1 whenever a single agent executes a move.
*   **Round-Robin Execution**: Agents act sequentially. In a fleet of 5, one full cycle of moves equals 5 global ticks.
*   **Termination**: The simulation ends when all objects are delivered, all agents run out of battery, or the maximum tick limit is reached.

### Reward Signal & Urgency
The simulation computes a global **Score** each tick using the formula:

```
Score = (delivered / total × 1000) - (ticks / max_ticks × 200)
```

This score rewards delivery ratio (up to 1000 pts) and applies a light time penalty (up to 200 pts). A full delivery at any tick always scores ≥ 800. The simulation broadcasts a **Reward Signal** to all agents containing:
*   **Time Pressure** (`0.0 → 1.0`): How much of the tick budget has been consumed.
*   **Collection Ratio** (`0.0 → 1.0`): Fraction of objects already collected.
*   **Urgency** (`time_pressure × (1 - collection_ratio)`): Combined signal that's high when time is running out AND objects still remain.

Agents use the urgency signal to modulate their heuristics:
*   **Scouts**: Expand their communication range under high urgency, sharing object locations more eagerly.
*   **Collectors**: Lower their distance threshold to the Coordinator under high urgency (> 0.5) to seek new tasks faster.
*   **A\* Pathfinding**: Unknown cell cost decreases with urgency, encouraging risk-taking through fog.
*   **Exploration**: Backtracking penalty increases with urgency for more linear movement. Frontier scoring weights distance more heavily to prefer closer targets.

## Execution Modes & GUI
The simulation can be run in two main modes:

1. **Interactive GUI (Default)**: A PyQt5-based interface that streamlines the simulation setup. Users can easily configure key parameters without modifying the code, including Map Selection, Agent Roles & Strategies, and global settings like maximum ticks and battery capacity.
2. **Headless CLI**: For automated testing or running with predefined configurations from `src/config.py`, bypass the GUI using the `--cli` flag.

## Map Environments
The physical environments for the simulation are defined in JSON format inside the `data/` directory (e.g., `A.json`, `B.json`). These files specify the grid dimensions, the layout of walls, warehouse entries/exits, and the ground truth coordinates of the objects to be collected.

## Analysis & Visualization
Upon completion, the simulation generates a log file (e.g., `log_A.json` or `log_B.json`) containing the step-by-step state of every agent and object. This data can be processed through two dedicated tools:

### Interactive Visualizer (`visualize_simulation.py`)
A comprehensive PyPlot-based visualizer that overlays the logs onto the map grid. It features:
*   **Playback Controls**: Interactive slider, Play/Pause, and Step forward/backward.
*   **Agent HUD**: Click on any agent to view its specific Field of View, current Battery, specific Role/Strategy, and carrying status.
*   **Real-time Metrics**: Displays the current tick, remaining objects, and total score.

### Log Analysis (`analyze_logs.py`)
A script that parses the execution logs to extract swarm performance metrics:
*   **Coverage**: Calculates the total "Swarm Cumulative Coverage" percentage.
*   **Delivery Metrics**: Tracks the number of objects successfully delivered by each agent.
*   **Efficiency**: Measures the unique cells visited and detects if/when agents get stuck.

## Getting Started
### Prerequisites
*   Python 3.x
*   Numpy, Matplotlib, PyQt5

### Installation
1. Activate your virtual environment: `.\.venv\bin\Activate.ps1`
2. Install dependencies: `pip install -r requirements.txt`

### Running the Project
Launch the GUI:
```bash
python main.py
```
Or run directly in CLI mode:
```bash
python main.py --cli
```
