# Simulation Configuration Constants
from src.enums import AgentRole
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

# Agent Role Mapping
AGENT_ROLES = {
    0: AgentRole.COLLECTOR,
    1: AgentRole.COLLECTOR,
    2: AgentRole.COLLECTOR,
    3: AgentRole.COLLECTOR,
    4: AgentRole.COLLECTOR
}

# Battery capacity per agent (scaled with MAX_TICKS)
# Formula: Battery = MAX_TICKS / NUM_AGENTS
BATTERY_CAPACITY = MAX_TICKS // NUM_AGENTS

# Visualization Settings
GRID_SIZE = 25
VISION_RANGE = 3
COMM_RANGE = 2
