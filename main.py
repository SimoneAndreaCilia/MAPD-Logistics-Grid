import os
import sys

# Let's make sure python finds the MAPD_Logistics/src directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.environment import Environment
from src.agent import Agent
from src.strategies import FrontierStrategy, RandomTargetStrategy
from src.simulation import Simulation

# Pipeline components
from analyze_logs import analyze_log
from visualize_simulation import run_visualizer

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, "data", "A.json")
    log_path = os.path.join(base_path, "log_A.json")
    
    if not os.path.exists(json_path):
        print(f"Error: The environment file {json_path} does not exist.")
        # Try finding it in parent dir
        json_path_alt = os.path.join(base_path, "..", "A.json")
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
    # Generate 5 agents
    for i in range(5):
        # Battery is 150 because max_ticks is 750 (1/5 ratio as requested)
        agent = Agent(agent_id=i, env_size=env.grid_size, vision_range=3, comm_range=2, battery=150)
        # Assign strategies: 3 frontier explorers, 2 random guided movements
        if i < 3:
            agent.set_strategy(FrontierStrategy())
        else:
            agent.set_strategy(RandomTargetStrategy())
        agents.append(agent)
        
    print(">>> Simulation Start...")
    sim = Simulation(env, agents, max_ticks=750)
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
