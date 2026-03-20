import json
import sys
import os

def analyze_log(log_path):
    if not os.path.exists(log_path):
        print(f"Error: Log file not found at {log_path}")
        return

    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    ticks = log_data
    print(f"\n>>> Analyzing Logs: {log_path}")
    print(f"Total ticks: {len(ticks)}")
    
    from collections import defaultdict
    
    agent_carrying_history = defaultdict(list)
    agent_paths = defaultdict(list)
    agent_stuck_count = defaultdict(int)
    
    current_pickup_tick = defaultdict(lambda: None)
    deliveries_count = defaultdict(int)
    
    # We'll collect agent IDs to iterate over them for summary at the end
    agent_ids = set()
    
    for tick in ticks:
        tick_num = tick['tick']
        agents = tick['agents']
        
        for agent in agents:
            a_id = agent['id']
            agent_ids.add(a_id)
            pos = agent['pos']
            carrying = agent['carrying_object']
            
            # Record paths for EVERY tick for better analysis (removed the %5 constraint)
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
    for a_id in sorted(agent_ids):
        path = agent_paths[a_id]
        agent_visited = set(tuple(p) for p in path)
        all_visited.update(agent_visited)
        unique_cells = len(agent_visited)
        print(f"Agent {a_id}: Unique cells visited: {unique_cells}, Stuck ticks: {agent_stuck_count[a_id]}, Objects delivered: {deliveries_count[a_id]}")
    
    # Using 357 as a hardcoded grid search area from previous logs, but could be dynamic
    # For now keeping it consistent with user's logic
    print(f"\nSwarm Cumulative Coverage: {len(all_visited)} / 357 ({len(all_visited)/357*100:.1f}%)")

if __name__ == '__main__':
    base_path = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_path, 'log_A.json')
    analyze_log(log_path)
