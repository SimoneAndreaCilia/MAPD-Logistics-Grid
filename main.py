import os
import sys
import argparse
import random
from typing import Dict, Any, List

# Ensure MAPD_Logistics/src is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.environment import Environment
from src.agent import Agent
from src.enums import AgentRole
from src.strategies import FrontierStrategy, RandomTargetStrategy, WallFollowerStrategy, SpiralStrategy, GreedyStrategy
from src.simulation import Simulation
from src.config import *

# Pipeline components
from analyze_logs import analyze_log
from visualize_simulation import run_visualizer

def run_simulation(config: Dict[str, Any], show_vis: bool = True):
    """
    Executes the simulation pipeline with provided configuration.
    
    Args:
        config: Dictionary containing simulation parameters.
        show_vis: Whether to launch the standalone visualizer window.
        
    Returns:
        tuple: (log_path, json_path) of the generated files.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    # For now, we still use MAP_NAME from config or default to 'B'
    map_name = config.get("map_name", MAP_NAME)
    json_path = os.path.join(base_path, "data", f"{map_name}.json")
    log_path = os.path.join(base_path, f"log_{map_name}.json")
    
    if not os.path.exists(json_path):
        print(f"Error: The environment file {json_path} does not exist.")
        return None, None

    print(f"\n>>> Executing Simulation: {map_name}")
    print(f">>> Agents: {config['num_agents']}, Ticks: {config['duration']}, Battery: {config['battery']}")
    
    env = Environment(json_path)
    
    strategy_factory = {
        "Frontier": FrontierStrategy,
        "WallFollower": WallFollowerStrategy,
        "Spiral": SpiralStrategy,
        "Greedy": GreedyStrategy,
        "RandomTarget": RandomTargetStrategy
    }
    
    agents = []
    # Role mapping from config (list of strings)
    role_options = [AgentRole(r) for r in config["roles"]]
    strategy_class = strategy_factory.get(config["strategy"], FrontierStrategy)

    for i in range(config["num_agents"]):
        # Cycle through chosen roles
        role = role_options[i % len(role_options)]
        
        agent = Agent(
            agent_id=i, 
            env_size=env.grid_size, 
            vision_range=VISION_RANGE, 
            comm_range=COMM_RANGE, 
            battery=config["battery"], 
            role=role
        )
        agent.set_strategy(strategy_class())
        agents.append(agent)
        
    sim = Simulation(env, agents, max_ticks=config["duration"])
    sim.run(log_path=log_path)
    
    print(">>> Stage 2: Log Analysis...")
    analyze_log(log_path)

    if show_vis:
        print(">>> Stage 3: Visualization Overlay...")
        try:
            run_visualizer(log_path=log_path, env_path=json_path)
        except Exception as e:
            print(f"Error starting visualizer: {e}")
            
    return log_path, json_path

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Logistics Grid Simulation")
    parser.add_argument("--gui", action="store_true", help="Launch the configuration GUI")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode using config.py")
    args = parser.parse_args()

    # Default to GUI if no arguments provided or --gui is set
    if args.gui or not args.cli:
        print(">>> Launching Configuration GUI...")
        try:
            from gui.main_window import launch_gui
            launch_gui(start_callback=run_simulation)
        except ImportError as e:
            print(f"Error: Could not load GUI components. {e}")
            print("Fallback to CLI mode...")
            args.cli = True

    if args.cli:
        print(">>> Running in CLI Mode (using src/config.py)...")
        # Map src/config.py values to config dict
        cli_config = {
            "num_agents": NUM_AGENTS,
            "duration": MAX_TICKS,
            "battery": BATTERY_CAPACITY,
            "roles": [r.value for r in set(AGENT_ROLES.values())], # Unique roles from config
            "strategy": "Frontier", # Default or derived
            "map_name": MAP_NAME
        }
        run_simulation(cli_config)

if __name__ == "__main__":
    main()
