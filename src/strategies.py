from __future__ import annotations
import random
from collections import deque
import numpy as np
import heapq
from typing import List, Tuple, Dict, Optional, Set, Any, TYPE_CHECKING
from .enums import AgentRole, CellType, AgentState

if TYPE_CHECKING:
    from .agent import Agent
    from .environment import Environment

def get_neighbors(pos: Tuple[int, int], grid_shape: Tuple[int, int]) -> List[Tuple[int, int]]:
    r, c = pos
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < grid_shape[0] and 0 <= nc < grid_shape[1]:
            neighbors.append((nr, nc))
    random.shuffle(neighbors)
    return neighbors

def a_star_path(
    local_map: np.ndarray, 
    start: Tuple[int, int], 
    targets: List[Tuple[int, int]], 
    traversable_vals: List[int], 
    visited_counts: Optional[Dict[Tuple[int, int], int]] = None, 
    strictly_known: bool = False
) -> Optional[List[Tuple[int, int]]]:
    """
    Finds the shortest path to the nearest target using A* algorithm.
    Uses weighted costs to prefer known corridors and avoid warehouses/unknowns.
    If visited_counts is provided, it penalizes heavily visited cells.
    """
    if not targets:
        return None
        
    traversable = set(traversable_vals)
    if strictly_known and CellType.UNKNOWN in traversable:
        traversable.remove(CellType.UNKNOWN)
        
    def h(pos):
        return min(abs(pos[0]-t[0]) + abs(pos[1]-t[1]) for t in targets)

    # Weighted costs based on cell type and visited frequency
    def get_cost(cell_val, pos):
        base_cost = 1
        if cell_val == CellType.CORRIDOR:  base_cost = 1   # Known Corridor
        elif cell_val == CellType.UNKNOWN:  base_cost = 3  # Unknown: prefer known corridors
        elif cell_val in [CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT]: base_cost = 10  # Warehouse zone: avoid if possible
        
        # Add penalty for visits to encourage fresh paths
        visit_penalty = 0
        if visited_counts is not None and pos in visited_counts:
            # Quadratic penalty to strongly discourage backtracking
            visit_penalty = (visited_counts[pos] ** 2) * 0.5
            
        return base_cost + visit_penalty

    open_set = []
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
            if cell_val in traversable:
                cost = get_cost(cell_val, n_pos)
                tentative_g = g_score[current] + cost
                if n_pos not in g_score or tentative_g < g_score[n_pos]:
                    came_from[n_pos] = current
                    g_score[n_pos] = tentative_g
                    f_score = tentative_g + h(n_pos)
                    heapq.heappush(open_set, (f_score, n_pos))
                    
    return None

class BaseStrategy:
    def get_next_move(self, agent: Agent, env: Environment) -> Optional[Tuple[int, int]]:
        raise NotImplementedError
        
    def get_priority_move(self, agent: Agent) -> Optional[Tuple[int, int]]:
        """
        Standard priority logic for all strategies:
        1. If carrying an object, go to nearest warehouse.
        2. If knows an object and is Collector, go to it (FETCHING).
        """
        # 1. Carrying an object? Return to warehouse ENTRANCE (3)
        if agent.carrying_object:
            agent.state = AgentState.DELIVERING
            # Target ONLY entrance cells (3)
            warehouse_entrances = set(zip(*np.where(agent.local_map == CellType.ENTRANCE)))
            if warehouse_entrances:
                # Include 2 (warehouse) in traversable_vals so agents can move inside if they are there
                path = a_star_path(agent.local_map, agent.pos, warehouse_entrances, [CellType.CORRIDOR, CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT, CellType.UNKNOWN], visited_counts=agent.visited_cells)
                if path: return path[0]
                
        # 1.5. Inside a warehouse (2, 3, 4) without an object? Head out!
        elif not agent.carrying_object and agent.local_map[agent.pos] in [CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT]:
             agent.state = AgentState.EXITING
             current_type = agent.local_map[agent.pos]
             
             if current_type == CellType.EXIT:
                 # At the exit cell, target the nearest known corridor
                 corridors = set(zip(*np.where(agent.local_map == CellType.CORRIDOR)))
                 if corridors:
                     # Allow moving from EXIT to CORRIDOR
                     path = a_star_path(agent.local_map, agent.pos, corridors, [CellType.CORRIDOR, CellType.EXIT], visited_counts=agent.visited_cells)
                     if path: return path[0]
             else:
                 # Inside the warehouse, target the nearest known exit cell (4)
                 warehouse_exits = set(zip(*np.where(agent.local_map == CellType.EXIT)))
                 if warehouse_exits:
                     path = a_star_path(agent.local_map, agent.pos, warehouse_exits, [CellType.CORRIDOR, CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT, CellType.UNKNOWN], visited_counts=agent.visited_cells)
                     if path: return path[0]
                 else:
                     # If exit 4 is not yet known, fallback to any corridor 0
                     corridors = set(zip(*np.where(agent.local_map == CellType.CORRIDOR)))
                     if corridors:
                         path = a_star_path(agent.local_map, agent.pos, corridors, [CellType.CORRIDOR, CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT, CellType.UNKNOWN], visited_counts=agent.visited_cells)
                         if path: return path[0]
                
        # 2. Knows objects and not a Scout? Go to the nearest one
        elif agent.known_objects and agent.role != AgentRole.SCOUT:
            agent.state = AgentState.FETCHING
            path = a_star_path(agent.local_map, agent.pos, agent.known_objects, [CellType.CORRIDOR, CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT, CellType.UNKNOWN], visited_counts=agent.visited_cells)
            if path: return path[0]

        # 2.5. Scout knows objects? RENDEZVOUS with nearest Collector to share data
        elif agent.known_objects and agent.role == AgentRole.SCOUT:
            # Filter last_known_others for Collectors
            collectors = [info for info in agent.last_known_others.values() if info.get("role") == AgentRole.COLLECTOR]
            if collectors:
                agent.state = AgentState.RENDEZVOUS
                collector_positions = [c["pos"] for c in collectors]
                # Find nearest collector position to the agent
                nearest_collector_pos = min(collector_positions, key=lambda p: abs(p[0]-agent.pos[0]) + abs(p[1]-agent.pos[1]))
                path = a_star_path(agent.local_map, agent.pos, [nearest_collector_pos], [CellType.CORRIDOR, CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT, CellType.UNKNOWN], visited_counts=agent.visited_cells)
                if path: return path[0]
            
        agent.state = AgentState.EXPLORING
        return None

    def get_frontier_cells(self, agent: Agent) -> List[Tuple[int, int]]:
        """
        Identifies cells that are known and traversable, but adjacent to unknown (-1) cells.
        """
        # Only consider corridors (type 0) as potential sources for new frontiers.
        # This prevents agents from venturing into warehouses to resolve unknown cells.
        traversable_mask = (agent.local_map == CellType.CORRIDOR)
        unknown_mask = (agent.local_map == -1)
        
        # A cell is a frontier if it is traversable AND has at least one unknown neighbor
        frontier = []
        rows, cols = np.where(traversable_mask)
        for r, c in zip(rows, cols):
            # Check neighbors
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < agent.local_map.shape[0] and 0 <= nc < agent.local_map.shape[1]:
                    if agent.local_map[nr, nc] == -1:
                        frontier.append((r, c))
                        break
        return frontier

    def get_exploration_move(self, agent: Agent) -> Tuple[int, int]:
        """
        Fallback exploration move using the visited_cells heatmap to avoid traps.
        Prioritizes neighbors leading towards the nearest frontier and penalizes backtracking.
        """
        neighbors = get_neighbors(agent.pos, agent.local_map.shape)
        # Include 2 to prevent stalls in warehouses
        valid_moves = [n for n in neighbors if agent.local_map[n[0], n[1]] in [CellType.UNKNOWN, CellType.CORRIDOR, CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT]]
        
        if not valid_moves:
            return agent.pos
            
        # 1. Prefer unknown cells above anything else if adjacent
        unknown_adjacent = [m for m in valid_moves if agent.local_map[m[0], m[1]] == -1]
        if unknown_adjacent:
            return random.choice(unknown_adjacent)

        # 2. Score candidates: base score is visit count. 
        # Add a penalty for backtracking to the previous position to prevent 2-cell oscillation.
        def get_move_score(move):
            score = agent.visited_cells.get(move, 0)
            if move == agent.last_pos:
                score += 10 # High penalty for backtracking to prevent oscillations
                
            # Momentum bonus: prefer moving in the same direction
            if agent.last_pos:
                current_dir = (agent.pos[0] - agent.last_pos[0], agent.pos[1] - agent.last_pos[1])
                move_dir = (move[0] - agent.pos[0], move[1] - agent.pos[1])
                if current_dir == move_dir:
                    score -= 0.5 # Small bonus for continuing in same direction
                    
            if move in agent.nearby_agents:
                score += 3 # Soft repulsion
                
            # EXPLORATION OPTIMIZATION: Avoid warehouses unless necessary
            if agent.state == AgentState.EXPLORING:
                cell_type = agent.local_map[move[0], move[1]]
                if cell_type in [CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT]:
                    score += 15 # High penalty for entering warehouses while exploring
            return score

        min_score = min(get_move_score(m) for m in valid_moves)
        best_candidates = [m for m in valid_moves if get_move_score(m) <= min_score + 0.5] # Allow near-ties
        
        # 3. Tie-breaker: pick one that leads DEEPER into the grid (further from (0,0))
        # and closer to a frontier.
        frontier = self.get_frontier_cells(agent)
        if frontier:
            def dist_to_frontier(pos):
                return min(abs(pos[0]-f[0]) + abs(pos[1]-f[1]) for f in frontier)
            
            # Quadrant Bias: Each agent targets a different corner to promote swarm spread
            # Agent 0: Top-Right (0, max), Agent 1: Bottom-Left (max, 0), 
            # Agent 2: Bottom-Right (max, max), Agent 3: Top-Left (0, 0),
            # Agent 4: Mid-Bottom (max, max//2)
            grid_h, grid_w = agent.local_map.shape
            quadrant_targets = [
                (0, grid_w-1),   # 0: Top-Right
                (grid_h-1, 0),   # 1: Bottom-Left
                (grid_h-1, grid_w-1), # 2: Bottom-Right
                (0, 0),          # 3: Top-Left
                (grid_h-1, grid_w//2) # 4: Mid-Bottom
            ]
            target_q = quadrant_targets[agent.id % 5]
            
            def depth_score(pos):
                # Distance to the assigned quadrant corner
                return abs(pos[0]-target_q[0]) + abs(pos[1]-target_q[1])
            
            best_candidates.sort(key=lambda m: (dist_to_frontier(m), depth_score(m), random.random()))
            return best_candidates[0]
        return random.choice(best_candidates)

    def get_coordination_move(self, agent: Agent) -> Optional[Tuple[int, int]]:
        """
        If idle, try to move toward the last known position of another agent to share maps.
        """
        if agent.last_known_others:
            # Pick a random last known metadata of another agent
            target_agent_id = random.choice(list(agent.last_known_others.keys()))
            target_info = agent.last_known_others[target_agent_id]
            target_pos = target_info["pos"]
            
            # Don't path if already close
            if abs(agent.pos[0] - target_pos[0]) + abs(agent.pos[1] - target_pos[1]) > agent.comm_range:
                # Use strictly_known=True for safer coordination pathfinding
                path = a_star_path(agent.local_map, agent.pos, [target_pos], [CellType.CORRIDOR, CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT, CellType.UNKNOWN], visited_counts=agent.visited_cells, strictly_known=True)
                if path: return path[0]
        return None

class RandomTargetStrategy(BaseStrategy):
    def get_next_move(self, agent: Agent, env: Environment) -> Optional[Tuple[int, int]]:
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
    def get_next_move(self, agent: Agent, env: Environment) -> Optional[Tuple[int, int]]:
        # Priorities (Package/Objects)
        move = self.get_priority_move(agent)
        if move: return move
        
        # Target persistence: keep current target until reached
        frontier = self.get_frontier_cells(agent)
        
        if agent.current_target:
            # We only clear the target if we reached it.
            # (decide_and_move also clears it if path fails or reached)
            if agent.pos == agent.current_target:
                agent.current_target = None
            # Or if it somehow became a wall (1) which shouldn't happen for frontiers
            elif agent.local_map[agent.current_target] == CellType.WALL:
                agent.current_target = None
                
        if not agent.current_target and frontier:
            # Quadrant Bias: Target frontiers closer to the assigned quadrant corner
            grid_h, grid_w = agent.local_map.shape
            quadrant_targets = [
                (0, grid_w-1),   # 0: Top-Right
                (grid_h-1, 0),   # 1: Bottom-Left
                (grid_h-1, grid_w-1), # 2: Bottom-Right
                (0, 0),          # 3: Top-Left
                (grid_h-1, grid_w//2) # 4: Mid-Bottom
            ]
            target_q = quadrant_targets[agent.id % 5]
            
            # Sort frontiers by Weighted Distance (Real Distance + Quadrant Bias + Stochastics)
            def score_frontier(f):
                dist = abs(f[0]-agent.pos[0]) + abs(f[1]-agent.pos[1])
                q_dist = abs(f[0]-target_q[0]) + abs(f[1]-target_q[1])
                # Small random factor to prevent agents from choosing the same cell
                return dist + (q_dist * 0.5) + random.uniform(0, 5)
            
            frontier.sort(key=score_frontier)
            agent.current_target = frontier[0]
            
        if agent.current_target:
            # Try to reach the target using A* with visited penalization
            path = a_star_path(agent.local_map, agent.pos, [agent.current_target], [CellType.CORRIDOR, CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT, CellType.UNKNOWN], visited_counts=agent.visited_cells, strictly_known=False)
            
            if path:
                return path[0]
            else:
                agent.current_target = None # Path unreachable, reset
            
        # Coordination (Map Sharing) - lower priority than frontier exploration
        if random.random() < 0.1: 
            move = self.get_coordination_move(agent)
            if move: return move
            
        # Fallback (Heatmap exploration)
        return self.get_exploration_move(agent)
