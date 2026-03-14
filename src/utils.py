import json

def manhattan_distance(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def get_line_of_sight_cells(pos1, pos2):
    """
    Returns the cells intersected by a straight line (Bresenham) between pos1 and pos2.
    """
    r1, c1 = pos1
    r2, c2 = pos2
    cells = []
    
    dr = abs(r2 - r1)
    dc = abs(c2 - c1)
    sr = 1 if r1 < r2 else -1
    sc = 1 if c1 < c2 else -1
    
    err = dr - dc
    
    while True:
        cells.append((r1, c1))
        if r1 == r2 and c1 == c2:
            break
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r1 += sr
        if e2 < dr:
            err += dr
            c1 += sc
            
    return cells

def has_line_of_sight(env, pos1, pos2):
    """
    Check if there is Line of Sight (no walls in between) between pos1 and pos2.
    """
    cells = get_line_of_sight_cells(pos1, pos2)
    # Check only intermediate cells to allow "seeing" the target cell even if it is a wall
    for r, c in cells[1:-1]:
        if env.is_obstacle((r, c)):
            return False
    return True

def get_visible_cells(env, pos, vision_range):
    """
    Returns a list of coordinates visible to the agent,
    within vision_range (Manhattan) and not occluded by walls.
    """
    visible = []
    r_center, c_center = pos
    
    for r in range(r_center - vision_range, r_center + vision_range + 1):
        for c in range(c_center - vision_range, c_center + vision_range + 1):
            target = (r, c)
            if env.in_bounds(target):
                if manhattan_distance(pos, target) <= vision_range:
                    if has_line_of_sight(env, pos, target):
                        visible.append(target)
                        
    return visible

class SimulationLogger:
    def __init__(self):
        self.log_data = []
        
    def add_tick_state(self, tick, agents, score, objects_left):
        """
        Saves the state at the current tick.
        agents = [{"id": a.id, "pos": a.pos, "battery": a.battery, "carrying": bool}]
        """
        state = {
            "tick": tick,
            "agents": agents,
            "score": score,
            "objects_left": objects_left
        }
        self.log_data.append(state)
        
    def save_log(self, filepath):
        with open(filepath, 'w') as f:
            json.dump(self.log_data, f, indent=2)
