import os
import sys

# Let's make sure python finds the MAPD_Logistics/src directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.environment import Environment
from src.agent import Agent
from src.enums import AgentRole
from src.strategies import FrontierStrategy, RandomTargetStrategy, WallFollowerStrategy, SpiralStrategy, GreedyStrategy
from src.simulation import Simulation
from src.config import MAX_TICKS, NUM_AGENTS, BATTERY_CAPACITY, VISION_RANGE, COMM_RANGE, MAP_NAME, AGENT_STRATEGIES

# Pipeline components
from analyze_logs import analyze_log
from visualize_simulation import run_visualizer

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, "data", f"{MAP_NAME}.json")
    log_path = os.path.join(base_path, f"log_{MAP_NAME}.json")
    
    if not os.path.exists(json_path):
        print(f"Error: The environment file {json_path} does not exist.")
        # Try finding it in parent dir
        json_path_alt = os.path.join(base_path, "..", f"{MAP_NAME}.json")
        if os.path.exists(json_path_alt):
            print(f"Found in fallback: {json_path_alt}")
            json_path = json_path_alt
        else:
            return

    print(">>> Stage 1: Simulation Execution...")
    env = Environment(json_path)
    print(f"Grid Size: {env.grid_size}x{env.grid_size}")
    print(f"Objects to find: {len(env.get_ground_truth_objects())}")
    
    print(">>> Agent Initialization...")
    agents = []
    
    def get_strategy(name):
        if name == "WallFollower": return WallFollowerStrategy()
        elif name == "Spiral": return SpiralStrategy()
        elif name == "Greedy": return GreedyStrategy()
        elif name == "RandomTarget": return RandomTargetStrategy()
        else: return FrontierStrategy()
        
    # Generate agents based on configuration
    for i in range(NUM_AGENTS):
        role = AgentRole.COLLECTOR
        strategy_name = AGENT_STRATEGIES.get(i % len(AGENT_STRATEGIES), "Frontier")
        strategy = get_strategy(strategy_name)
        
        agent = Agent(
            agent_id=i, 
            env_size=env.grid_size, 
            vision_range=VISION_RANGE, 
            comm_range=COMM_RANGE, 
            battery=BATTERY_CAPACITY, 
            role=role
        )
        agent.set_strategy(strategy)
        agents.append(agent)
        
    print(">>> Simulation Start...")
    sim = Simulation(env, agents, max_ticks=MAX_TICKS)
    sim.run(log_path=log_path)
    print(">>> Simulation Finished.")

    print("\n>>> Stage 2: Log Analysis...")
    analyze_log(log_path)

    print("\n>>> Stage 3: Visualization...")
    try:
        run_visualizer(log_path=log_path, env_path=json_path)
    except Exception as e:
        print(f"Error starting visualizer: {e}")

if __name__ == "__main__":
    main()
