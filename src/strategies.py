import random
from collections import deque
import numpy as np
import heapq

def get_neighbors(pos, grid_shape):
    r, c = pos
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < grid_shape[0] and 0 <= nc < grid_shape[1]:
            neighbors.append((nr, nc))
    random.shuffle(neighbors)
    return neighbors

def a_star_path(local_map, start, targets, traversable_vals):
    """
    Finds the shortest path to the nearest target using A* algorithm.
    Allows traversing any value in `traversable_vals`.
    """
    if not targets:
        return None
        
    def h(pos):
        return min(abs(pos[0]-t[0]) + abs(pos[1]-t[1]) for t in targets)

    open_set = []
    # (f_score, pos)
    heapq.heappush(open_set, (h(start), start))
    came_from = {start: None}
    g_score = {start: 0}
    
    while open_set:
        _, current = heapq.heappop(open_set)
        
        if current in targets:
            path = []
            while current != start:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
            
        for n_pos in get_neighbors(current, local_map.shape):
            cell_val = local_map[n_pos[0], n_pos[1]]
            if cell_val in traversable_vals:
                tentative_g = g_score[current] + 1
                if n_pos not in g_score or tentative_g < g_score[n_pos]:
                    came_from[n_pos] = current
                    g_score[n_pos] = tentative_g
                    f_score = tentative_g + h(n_pos)
                    heapq.heappush(open_set, (f_score, n_pos))
                    
    return None

class BaseStrategy:
    def get_next_move(self, agent, env):
        raise NotImplementedError
        
    def get_priority_move(self, agent):
        """
        Standard priority logic for all strategies:
        1. If carrying an object, go to nearest warehouse.
        2. If knows an object and is Collector, go to it (FETCHING).
        """
        # 1. Carrying an object? Return to warehouse ENTRANCE (3)
        if agent.carrying_object:
            agent.state = "DELIVERING"
            # Target ONLY entrance cells (3)
            warehouse_entrances = set(zip(*np.where(agent.local_map == 3)))
            if warehouse_entrances:
                # Include -1 (unknown) and other warehouse cells in traversable_vals for pathfinding
                path = a_star_path(agent.local_map, agent.pos, warehouse_entrances, [0, 2, 3, 4, -1])
                if path: return path[0]
                
        # 1.5. Inside a warehouse without an object? Head to EXIT (4)
        elif not agent.carrying_object and agent.local_map[agent.pos[0], agent.pos[1]] in [2, 3]:
             agent.state = "EXITING"
             warehouse_exits = set(zip(*np.where(agent.local_map == 4)))
             if warehouse_exits:
                 path = a_star_path(agent.local_map, agent.pos, warehouse_exits, [0, 2, 3, 4, -1])
                 if path: return path[0]
                
        # 2. Knows objects and not a Scout? Go to the nearest one
        elif agent.known_objects and agent.role != "Scout":
            agent.state = "FETCHING"
            path = a_star_path(agent.local_map, agent.pos, agent.known_objects, [0, 2, 3, 4, -1])
            if path: return path[0]
            
        agent.state = "EXPLORING"
        return None

    def get_exploration_move(self, agent):
        """
        Fallback exploration move using the visited_cells heatmap to avoid traps.
        """
        neighbors = get_neighbors(agent.pos, agent.local_map.shape)
        # Avoid walls (1), allow empty (0), entrances (3/4), and unknown (-1)
        valid_moves = [n for n in neighbors if agent.local_map[n[0], n[1]] in [-1, 0, 3, 4]]
        
        if not valid_moves:
            return agent.pos
            
        # Sort by visit count (least visited first)
        valid_moves.sort(key=lambda m: agent.visited_cells.get(m, 0))
        min_visits = agent.visited_cells.get(valid_moves[0], 0)
        best_candidates = [m for m in valid_moves if agent.visited_cells.get(m, 0) == min_visits]
        
        return random.choice(best_candidates)

    def get_coordination_move(self, agent):
        """
        If idle, try to move toward the last known position of another agent to share maps.
        """
        if agent.last_known_others:
            # Pick a random last known position of another agent
            target_agent_id = random.choice(list(agent.last_known_others.keys()))
            target_pos = agent.last_known_others[target_agent_id]
            
            # Don't path if already close
            if abs(agent.pos[0] - target_pos[0]) + abs(agent.pos[1] - target_pos[1]) > agent.comm_range:
                path = a_star_path(agent.local_map, agent.pos, [target_pos], [0, 2, 3, 4, -1])
                if path: return path[0]
        return None

class RandomTargetStrategy(BaseStrategy):
    def get_next_move(self, agent, env):
        # Priorities (Package/Objects)
        move = self.get_priority_move(agent)
        if move: return move
        
        # Coordination (Map Sharing)
        if random.random() < 0.3: # 30% chance to seek others if idle
            move = self.get_coordination_move(agent)
            if move: return move
            
        # Fallback (Heatmap exploration)
        return self.get_exploration_move(agent)

class FrontierStrategy(BaseStrategy):
    def get_next_move(self, agent, env):
        # Priorities (Package/Objects)
        move = self.get_priority_move(agent)
        if move: return move
        
        # Search for the nearest unknown cell (-1)
        unknown_cells = set(zip(*np.where(agent.local_map == -1)))
        if unknown_cells:
            path = a_star_path(agent.local_map, agent.pos, unknown_cells, [0, 2, 3, 4, -1])
            if path: return path[0]
            
        # Coordination (Map Sharing)
        if random.random() < 0.2: 
            move = self.get_coordination_move(agent)
            if move: return move
            
        # Fallback (Heatmap exploration)
        return self.get_exploration_move(agent)
