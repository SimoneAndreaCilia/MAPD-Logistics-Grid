# Simulation Configuration Constants
from src.enums import AgentRole
# Total number of ticks for the simulation
MAX_TICKS = 500

# Map to use (A, B, etc.)
MAP_NAME = "B"

# Number of agents in the swarm
NUM_AGENTS = 5

# Agent Strategy Mapping that you can choose between
# "Frontier", "WallFollower", "Spiral", "Greedy", "RandomTarget"

AGENT_STRATEGIES = {
    0: "Frontier",
    1: "WallFollower",
    2: "Spiral",
    3: "Greedy",
    4: "RandomTarget"
}

# Agent Role Mapping that you can choose between
# "Scout", "Collector", "Coordinator"
AGENT_ROLES = {
    0: AgentRole.SCOUT,
    1: AgentRole.COLLECTOR,
    2: AgentRole.COLLECTOR,
    3: AgentRole.COLLECTOR,
    4: AgentRole.COLLECTOR
}

# Battery capacity per agent
BATTERY_CAPACITY = 500
BATTERY_LOW_THRESHOLD = 100

# Visualization Settings
GRID_SIZE = 25
VISION_RANGE = 3
COMM_RANGE = 2
