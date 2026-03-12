import json
import sys

def analyze_bouncing(log_path):
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    agent_paths = {i: [] for i in range(5)}
    
    if isinstance(log_data, dict):
        ticks = log_data.get('ticks', [])
    else:
        ticks = log_data
        
    for tick in ticks:
        agents = tick['agents']
        for agent in agents:
            agent_paths[agent['id']].append(tuple(agent['pos']))
            
    for a_id in range(5):
        path = agent_paths[a_id]
        print(f"\n--- Agent {a_id} top 20 moves ---")
        for i in range(1, min(21, len(path))):
            print(f"Move {i}: {path[i-1]} -> {path[i]}")

if __name__ == '__main__':
    log_path = r'c:\Develop_Projects\Artificial_Swarm_Intelligence_Project\MAPD_Logistics\log_A.json'
    analyze_bouncing(log_path)
