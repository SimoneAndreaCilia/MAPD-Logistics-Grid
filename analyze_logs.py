import json
import sys
import os
from collections import defaultdict

def analyze_log(log_path):
    if not os.path.exists(log_path):
        print(f"Error: Log file not found at {log_path}")
        return

    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    ticks = log_data
    if not ticks:
        print("Empty log file.")
        return

    print(f"\n>>> Analyzing Logs: {log_path}")
    print(f"Total ticks in log: {len(ticks)}")
    
    agent_paths = defaultdict(list)
    agent_stuck_count = defaultdict(int)
    current_pickup_tick = defaultdict(lambda: None)
    deliveries_count = defaultdict(int)
    
    # Initialization from first tick
    first_tick = ticks[0]
    last_positions = {a['id']: a['pos'] for a in first_tick['agents']}
    agent_ids = sorted(last_positions.keys())
    num_agents = len(agent_ids)
    
    # Store initial positions
    for a_id in agent_ids:
        agent_paths[a_id].append(last_positions[a_id])

    last_mover_id = -1
    
    # Process from second tick onwards
    for tick_idx in range(1, len(ticks)):
        tick = ticks[tick_idx]
        tick_num = tick['tick']
        agents = tick['agents']
        
        # Identify who moved in this tick
        current_mover_id = -1
        current_mover_pos = None
        current_mover_carrying = False
        
        for agent in agents:
            a_id = agent['id']
            if agent['pos'] != last_positions[a_id]:
                current_mover_id = a_id
                current_mover_pos = agent['pos']
                current_mover_carrying = agent['carrying_object']
                break
        
        if current_mover_id != -1:
            # Check for skipped turns in round-robin sequence
            if last_mover_id != -1:
                # Expected: (0->1->2->3->4->0)
                expected_mover = (last_mover_id + 1) % num_agents
                # We iterate until we find the current mover. 
                # Anyone skipped who is active is considered 'Stuck' for that turn.
                while expected_mover != current_mover_id:
                    # Is expected_mover active in this tick?
                    is_active = any(a['id'] == expected_mover and a.get('active', True) for a in agents)
                    if is_active:
                        agent_stuck_count[expected_mover] += 1
                    expected_mover = (expected_mover + 1) % num_agents
            
            # Record movement
            agent_paths[current_mover_id].append(current_mover_pos)
            last_positions[current_mover_id] = current_mover_pos
            last_mover_id = current_mover_id
            
            # Delivery / Pickup logic
            if current_mover_carrying and current_pickup_tick[current_mover_id] is None:
                current_pickup_tick[current_mover_id] = tick_num
                print(f"Tick {tick_num}: Agent {current_mover_id} picked up an object at {current_mover_pos}.")
                
            if not current_mover_carrying and current_pickup_tick[current_mover_id] is not None:
                took_ticks = tick_num - current_pickup_tick[current_mover_id]
                deliveries_count[current_mover_id] += 1
                print(f"Tick {tick_num}: Agent {current_mover_id} delivered object #{deliveries_count[current_mover_id]} at {current_mover_pos}. Took {took_ticks} ticks.")
                current_pickup_tick[current_mover_id] = None

    print("\n--- Summary ---")
    all_visited = set()
    first_tick_info = {a['id']: a for a in ticks[0]['agents']}
    
    for a_id in agent_ids:
        path = agent_paths[a_id]
        agent_visited = set(tuple(p) for p in path)
        all_visited.update(agent_visited)
        unique_cells = len(agent_visited)
        
        info = first_tick_info.get(a_id, {})
        role = info.get('role', '?')
        strategy = info.get('strategy', '?')
        
        print(f"Agent {a_id} [{role}/{strategy}]: Unique cells visited: {unique_cells}, Stuck turns: {agent_stuck_count[a_id]}, Objects delivered: {deliveries_count[a_id]}")
    
    # Coverage calculation (using hardcoded 357 from user's logs)
    print(f"\nSwarm Cumulative Coverage: {len(all_visited)} / 357 ({len(all_visited)/357*100:.1f}%)")

    total_delivered = sum(deliveries_count.values())
    last_tick = ticks[-1]
    objects_left = last_tick.get('objects_left', 0)
    total_objects = total_delivered + objects_left
    success_rate = (total_delivered / total_objects * 100) if total_objects > 0 else 100.0
    
    print(f"\n--- Performance Metrics ---")
    print(f"Success Rate: {total_delivered}/{total_objects} ({success_rate:.1f}%)")
    print(f"Final Score: {last_tick.get('score', 0)}")
    print(f"Score Formula: (delivered/total × 1000) - (ticks/max_ticks × 200)")

if __name__ == '__main__':
    base_path = os.path.dirname(os.path.abspath(__file__))
    log_file = sys.argv[1] if len(sys.argv) > 1 else 'log_B.json'
    log_path = os.path.join(base_path, log_file)
    analyze_log(log_path)
