"""
A verification script used to trace a specific agent's movement history 
after a delivery event, ensuring it correctly follows the exit protocol.
"""
import json

def verify_agent_exit(log_path, agent_id, delivery_tick):
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    # Check ticks from delivery_tick to delivery_tick + 50
    print(f"--- Path for Agent {agent_id} after delivery at tick {delivery_tick} ---")
    for tick in log_data[delivery_tick:delivery_tick+50]:
        for agent in tick['agents']:
            if agent['id'] == agent_id:
                pos = agent['pos']
                # Try to get state if available, but it's not in the basic log format usually
                # Our simulation.py might not log state. Let's check.
                print(f"Tick {tick['tick']}: Pos {pos}")

if __name__ == '__main__':
    verify_agent_exit('log_A.json', 2, 148)
