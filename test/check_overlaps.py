"""
This script analyzes simulation logs to detect any 'collisions' or overlaps,
where multiple agents occupied the same cell at the same time.
"""
import json

def check_overlaps(log_path):
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    overlap_ticks = []
    for tick_data in log_data:
        tick = tick_data['tick']
        positions = [tuple(a['pos']) for a in tick_data['agents'] if a['active']]
        if len(positions) != len(set(positions)):
            overlap_ticks.append(tick)
            # Find which positions overlap
            seen = set()
            duplicates = [x for x in positions if x in seen or seen.add(x)]
            print(f"Tick {tick}: Overlap at {duplicates}")
            
    if not overlap_ticks:
        print("No overlaps found in the log.")
    else:
        print(f"Total ticks with overlaps: {len(overlap_ticks)}")

if __name__ == "__main__":
    check_overlaps("log_A.json")
