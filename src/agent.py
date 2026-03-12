import numpy as np
from .utils import get_visible_cells, manhattan_distance

class Agent:
    def __init__(self, agent_id, env_size, vision_range=2, comm_range=2):
        self.id = agent_id
        self.pos = (0, 0)
        self.battery = 500
        self.vision_range = vision_range
        self.comm_range = comm_range
        
        self.carrying_object = False
        self.is_active = True
        
        # Local map: -1 indicates 'unknown'
        self.local_map = np.full((env_size, env_size), -1, dtype=int)
        # The starting cell is always a free corridor
        self.local_map[0, 0] = 0 
        
        # Set of coordinates of objects seen but not yet collected
        self.known_objects = set()
        
        # Track number of visits to each cell to avoid getting stuck
        self.visited_cells = {self.pos: 1}
        
        # Track last known positions of other agents to coordinate map sharing
        self.last_known_others = {}
        
        self.strategy = None

    def set_strategy(self, strategy):
        self.strategy = strategy

    def sense(self, env):
        if not self.is_active:
            return
            
        visible_cells = get_visible_cells(env, self.pos, self.vision_range)
        for r, c in visible_cells:
            # Update the map with the cell type
            self.local_map[r, c] = env.get_cell_type((r, c))
            
            # If it detects an object on the cell, it adds it to the known objects
            if env.has_object((r, c)) and not self.carrying_object:
                self.known_objects.add((r, c))

    def communicate(self, other_agents):
        if not self.is_active:
            return
            
        for other in other_agents:
            if other.id != self.id and other.is_active:
                dist = manhattan_distance(self.pos, other.pos)
                if dist <= self.comm_range:
                    # Merge local maps (takes the max, so it replaces -1)
                    self.local_map = np.maximum(self.local_map, other.local_map)
                    
                    # Share known objects
                    self.known_objects.update(other.known_objects)
                    
                # Update last known positions of all active agents
                if other.id != self.id and other.is_active:
                    self.last_known_others[other.id] = other.pos

    def decide_and_move(self, env):
        if not self.is_active or self.battery <= 0:
            self.is_active = False
            return False # No move made
            
        next_pos = self.strategy.get_next_move(self, env)
        
        if next_pos and next_pos != self.pos:
            self.pos = next_pos
            self.visited_cells[self.pos] = self.visited_cells.get(self.pos, 0) + 1
        else:
            print(f"Agent {self.id} stuck at {self.pos}. Strategy returned {next_pos}")
            
        # Picks up the object if he steps on it and has nothing in his hand
        if not self.carrying_object and env.has_object(self.pos):
            env.remove_object(self.pos)
            self.carrying_object = True
            if self.pos in self.known_objects:
                self.known_objects.remove(self.pos)
                
        # Drops off the object if it arrives at a warehouse
        # Warehouses have values 2 (internal), 3 (entrance), 4 (exit)
        cell_type = env.get_cell_type(self.pos)
        if self.carrying_object and cell_type in [2, 3, 4]:
            self.carrying_object = False
            
        self.battery -= 1
            
        if self.battery <= 0:
            self.is_active = False
            
        return True # Move/action made and costs 1 tick/energy
