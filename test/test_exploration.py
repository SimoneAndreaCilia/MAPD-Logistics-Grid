"""
A simulation integration test that calculates the swarm's combined 
map exploration percentage over time and plots the result.
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Ensure src is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.environment import Environment
from src.agent import Agent
from src.strategies import FrontierStrategy, RandomTargetStrategy
from src.simulation import Simulation

def calculate_exploration(agents, grid_size):
    # Merge all local maps
    combined_map = np.full((grid_size, grid_size), -1)
    for agent in agents:
        # Replace -1 with known values
        combined_map = np.maximum(combined_map, agent.local_map)
    
    known_count = np.count_nonzero(combined_map != -1)
    total_cells = grid_size * grid_size
    return (known_count / total_cells) * 100

def run_test():
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, "data", "A.json")
    
    env = Environment(json_path)
    grid_size = env.grid_size
    
    agents = []
    for i in range(5):
        agent = Agent(agent_id=i, env_size=grid_size, vision_range=3, comm_range=2, battery=500)
        if i < 3:
            agent.set_strategy(FrontierStrategy())
        else:
            agent.set_strategy(RandomTargetStrategy())
        agents.append(agent)
        
    sim = Simulation(env, agents, max_ticks=5000)
    
    stats = []
    last_exp = 0
    stall_ticks = 0
    
    # Run manual steps to capture stats
    while not sim.is_done:
        sim.step()
        if sim.current_tick % 50 == 0:
            exp_pct = calculate_exploration(agents, grid_size)
            stats.append((sim.current_tick, exp_pct))
            print(f"Tick {sim.current_tick}: Exploration {exp_pct:.2f}%")
            
            if exp_pct <= last_exp + 0.01:
                stall_ticks += 50
            else:
                stall_ticks = 0
                
            last_exp = exp_pct

            if exp_pct >= 95:
                print(f"Reached 95% exploration at tick {sim.current_tick}!")
                break
                
            if stall_ticks >= 500:
                print(f"STALLED: Exploration stalled at {exp_pct:.2f}% for {stall_ticks} ticks.")
                break
                
    # Final state
    sim.run(log_path=os.path.join(base_path, "test_log.json"))
    
    # Plotting (requires matplotlib, otherwise just print)
    ticks = [s[0] for s in stats]
    pcts = [s[1] for s in stats]
    
    print("\n--- Summary ---")
    print(f"Final Tick: {sim.current_tick}")
    print(f"Final Exploration: {calculate_exploration(agents, grid_size):.2f}%")

if __name__ == "__main__":
    run_test()
