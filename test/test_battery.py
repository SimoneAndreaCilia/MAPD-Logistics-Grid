import os
import sys

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_path)

from src import config
config.MAX_TICKS = 300
config.BATTERY_CAPACITY = 80
config.BATTERY_LOW_THRESHOLD = 30
config.NUM_AGENTS = 5

from src.environment import Environment
from src.agent import Agent
from src.enums import AgentRole, CellType, AgentState
from src.strategies import FrontierStrategy, RandomTargetStrategy, WallFollowerStrategy, SpiralStrategy, GreedyStrategy
from src.simulation import Simulation

def test():
    json_path = os.path.join(base_path, "data", "B.json")
    if not os.path.exists(json_path):
        json_path = os.path.join(base_path, "data", "A.json")
        
    env = Environment(json_path)
    agents = []
    
    for i in range(config.NUM_AGENTS):
        agent = Agent(
            agent_id=i, 
            env_size=env.grid_size, 
            battery=config.BATTERY_CAPACITY, 
            vision_range=config.VISION_RANGE, 
            comm_range=config.COMM_RANGE, 
            role=AgentRole.COLLECTOR
        )
        agent.set_strategy(FrontierStrategy())
        
        # Artificially reveal the first warehouse entrance to the agent
        if env.warehouses:
            wr, wc = env.warehouses[0].entrance
            agent.local_map[wr, wc] = CellType.ENTRANCE
            for r, c in env.warehouses[0].area:
                agent.local_map[r, c] = CellType.WAREHOUSE
                
        agents.append(agent)
        
    sim = Simulation(env, agents, config.MAX_TICKS)
    sim.run(log_path="test_log.json")
    
    for a in agents:
        cell_str = CellType(env.get_cell_type(a.pos)).name
        print(f"Agent {a.id}: battery={a.battery}, active={a.is_active}, state={a.state.name}, pos={a.pos}, cell_type={cell_str}")

if __name__ == "__main__":
    test()
