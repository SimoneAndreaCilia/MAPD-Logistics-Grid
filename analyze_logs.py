import json
import sys

def analyze_log(log_path):
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    ticks = log_data
    print(f"Total ticks: {len(ticks)}")
    
    agent_carrying_history = {i: [] for i in range(5)}
    agent_paths = {i: [] for i in range(5)}
    agent_stuck_count = {i: 0 for i in range(5)}
    
    first_pickup = {}
    delivery_time = {}
    
    for tick in ticks:
        tick_num = tick['tick']
        agents = tick['agents']
        
        for agent in agents:
            a_id = agent['id']
            pos = agent['pos']
            carrying = agent['carrying_object']
            
            agent_paths[a_id].append(pos)
            
            if len(agent_paths[a_id]) > 1:
                # Check if stuck (same pos)
                if agent_paths[a_id][-1] == agent_paths[a_id][-2]:
                    agent_stuck_count[a_id] += 1
            
            if carrying and a_id not in first_pickup:
                first_pickup[a_id] = tick_num
                print(f"Tick {tick_num}: Agent {a_id} picked up an object at {pos}.")
                
            if not carrying and a_id in first_pickup and a_id not in delivery_time:
                # Delivered!
                delivery_time[a_id] = tick_num
                print(f"Tick {tick_num}: Agent {a_id} delivered an object at {pos}. Took {tick_num - first_pickup[a_id]} ticks.")

    print("\n--- Summary ---")
    for a_id in range(5):
        path = agent_paths[a_id]
        unique_cells = len(set(tuple(p) for p in path))
        print(f"Agent {a_id}: Unique cells visited: {unique_cells}, Stuck ticks: {agent_stuck_count[a_id]}")

if __name__ == '__main__':
    log_path = r'c:\Develop_Projects\Artificial_Swarm_Intelligence_Project\MAPD_Logistics\log_A.json'
    analyze_log(log_path)
