import random
from collections import deque
import numpy as np

def get_neighbors(pos, grid_shape):
    r, c = pos
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < grid_shape[0] and 0 <= nc < grid_shape[1]:
            neighbors.append((nr, nc))
    return neighbors

def bfs_path(local_map, start, targets, traversable_vals):
    """
    Finds the shortest path (list of moves) to reach the nearest `target`.
    """
    if not targets:
        return None
        
    queue = deque([start])
    came_from = {start: None}
    
    found_target = None
    
    while queue:
        current = queue.popleft()
        
        if current in targets:
            found_target = current
            break
            
        for n_pos in get_neighbors(current, local_map.shape):
            if n_pos not in came_from:
                cell_val = local_map[n_pos[0], n_pos[1]]
                if cell_val in traversable_vals:
                    came_from[n_pos] = current
                    queue.append(n_pos)
                    
    if not found_target:
        return None
        
    # Reconstructs the path
    path = []
    curr = found_target
    while curr != start:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    return path

class BaseStrategy:
    def get_next_move(self, agent, env):
        raise NotImplementedError

class RandomTargetStrategy(BaseStrategy):
    """
    It explores by moving randomly to adjacent free cells,
    but is overridden by pathfinding if it sees an item or needs to return to the warehouse.
    """
    def get_next_move(self, agent, env):
        # 1. If it carries a package, it looks for the nearest warehouse (types 2, 3, 4)
        if agent.carrying_object:
            warehouse_cells = set(zip(*np.where((agent.local_map == 2) | (agent.local_map == 3) | (agent.local_map == 4))))
            if warehouse_cells:
                # It can walk anywhere as long as it's not a wall (1).
                # The unknown (-1) does not count as safe walkable to avoid getting lost, 
                # but for now we only allow on known areas: 0, 2, 3, 4
                path = bfs_path(agent.local_map, agent.pos, warehouse_cells, [0, 2, 3, 4])
                if path:
                    return path[0] # Make the first step
            # If it doesn't know any warehouse, it explores randomly
            
        # 2. If it doesn't carry anything and knows objects, go to the nearest one
        elif agent.known_objects:
            path = bfs_path(agent.local_map, agent.pos, agent.known_objects, [0, 2, 3, 4, -1])
            if path:
                return path[0]
                
        # 3. Otherwise explore adjacent cells
        neighbors = get_neighbors(agent.pos, agent.local_map.shape)
        valid_moves = []
        for n in neighbors:
            # It also moves on the unknown or on empty spaces/entrance
            if agent.local_map[n[0], n[1]] in [-1, 0, 3, 4]:
                # Just a safety measure: avoid known walls.
                valid_moves.append(n)
                
        if valid_moves:
            return random.choice(valid_moves)
        return agent.pos

class FrontierStrategy(BaseStrategy):
    """
    Explores the 'Frontier' of the map, i.e., the known cells adjacent to unknown cells.
    """
    def get_next_move(self, agent, env):
        # Same priorities for packages/warehouses
        if agent.carrying_object:
            warehouse_cells = set(zip(*np.where((agent.local_map == 2) | (agent.local_map == 3) | (agent.local_map == 4))))
            if warehouse_cells:
                path = bfs_path(agent.local_map, agent.pos, warehouse_cells, [0, 2, 3, 4])
                if path: return path[0]
                
        elif agent.known_objects:
            path = bfs_path(agent.local_map, agent.pos, agent.known_objects, [0, 2, 3, 4, -1])
            if path: return path[0]
            
        # Search for the nearest unknown cell (-1)
        unknown_cells = set(zip(*np.where(agent.local_map == -1)))
        if unknown_cells:
            path = bfs_path(agent.local_map, agent.pos, unknown_cells, [0, 2, 3, 4, -1])
            if path:
                return path[0]
                
        # Fallback random
        neighbors = get_neighbors(agent.pos, agent.local_map.shape)
        valid_moves = []
        for n in neighbors:
            if agent.local_map[n[0], n[1]] in [-1, 0, 3, 4]:
                valid_moves.append(n)
        if valid_moves:
            return random.choice(valid_moves)
        return agent.pos
