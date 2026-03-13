import os
import sys

# Let's make sure python finds the MAPD_Logistics/src directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.environment import Environment
from src.agent import Agent
from src.strategies import FrontierStrategy, RandomTargetStrategy
from src.simulation import Simulation

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, "data", "A.json")
    
    if not os.path.exists(json_path):
        print(f"Error: The environment file {json_path} does not exist.")
        # Try finding it in parent dir
        json_path_alt = os.path.join(base_path, "..", "A.json")
        if os.path.exists(json_path_alt):
            print(f"Found in fallback: {json_path_alt}")
            json_path = json_path_alt
        else:
            return

    print(">>> Environment Initialization...")
    env = Environment(json_path)
    print(f"Grid Size: {env.grid_size}x{env.grid_size}")
    print(f"Objects to find: {len(env.get_ground_truth_objects())}")
    
    print(">>> Agent Initialization...")
    agents = []
    # Generate 5 agents
    for i in range(5):
        agent = Agent(agent_id=i, env_size=env.grid_size, vision_range=3, comm_range=2)
        # Assign strategies: 3 frontier explorers, 2 random guided movements
        if i < 3:
            agent.set_strategy(FrontierStrategy())
        else:
            agent.set_strategy(RandomTargetStrategy())
        agents.append(agent)
        
    print(">>> Simulation Start...")
    sim = Simulation(env, agents, max_ticks=750)
    sim.run(log_path=os.path.join(base_path, "log_A.json"))

if __name__ == "__main__":
    main()
