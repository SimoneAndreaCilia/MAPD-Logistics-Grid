# Simulation Configuration Constants

# Total number of ticks for the simulation
MAX_TICKS = 500

# Map to use (A, B, etc.)
MAP_NAME = "B"

# Number of agents in the swarm
NUM_AGENTS = 5

# Agent Strategy Mapping
AGENT_STRATEGIES = {
    0: "Frontier",
    1: "WallFollower",
    2: "Spiral",
    3: "Greedy",
    4: "RandomTarget"
}

# Battery capacity per agent (scaled with MAX_TICKS)
# Formula: Battery = MAX_TICKS / NUM_AGENTS
BATTERY_CAPACITY = MAX_TICKS // NUM_AGENTS

# Visualization Settings
GRID_SIZE = 25
VISION_RANGE = 3
COMM_RANGE = 2
