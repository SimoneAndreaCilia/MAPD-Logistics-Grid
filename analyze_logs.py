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
    
    current_pickup_tick = {i: None for i in range(5)}
    deliveries_count = {i: 0 for i in range(5)}
    
    for tick in ticks:
        tick_num = tick['tick']
        agents = tick['agents']
        
        for agent in agents:
            a_id = agent['id']
            pos = agent['pos']
            carrying = agent['carrying_object']
            
            if (tick_num - 1) % 5 == a_id:
                agent_paths[a_id].append(pos)
                
                if len(agent_paths[a_id]) > 1:
                    # Check if stuck (same pos as its last turn)
                    if agent_paths[a_id][-1] == agent_paths[a_id][-2]:
                        agent_stuck_count[a_id] += 1
            
            if carrying and current_pickup_tick[a_id] is None:
                current_pickup_tick[a_id] = tick_num
                print(f"Tick {tick_num}: Agent {a_id} picked up an object at {pos}.")
                
            if not carrying and current_pickup_tick[a_id] is not None:
                # Delivered!
                took_ticks = tick_num - current_pickup_tick[a_id]
                deliveries_count[a_id] += 1
                print(f"Tick {tick_num}: Agent {a_id} delivered object #{deliveries_count[a_id]} at {pos}. Took {took_ticks} ticks.")
                current_pickup_tick[a_id] = None # Reset for the next object

    print("\n--- Summary ---")
    all_visited = set()
    for a_id in range(5):
        path = agent_paths[a_id]
        agent_visited = set(tuple(p) for p in path)
        all_visited.update(agent_visited)
        unique_cells = len(agent_visited)
        print(f"Agent {a_id}: Unique cells visited: {unique_cells}, Stuck ticks: {agent_stuck_count[a_id]}, Objects delivered: {deliveries_count[a_id]}")
    
    print(f"\nSwarm Cumulative Coverage: {len(all_visited)} / 357 ({len(all_visited)/357*100:.1f}%)")

if __name__ == '__main__':
    log_path = r'c:\Develop_Projects\Artificial_Swarm_Intelligence_Project\MAPD_Logistics\log_A.json'
    analyze_log(log_path)
