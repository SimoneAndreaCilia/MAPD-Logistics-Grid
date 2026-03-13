import numpy as np
from .utils import get_visible_cells, manhattan_distance

class Agent:
    def __init__(self, agent_id, env_size, vision_range=2, comm_range=2, battery=100):
        self.id = agent_id
        self.pos = (0, 0)
        self.battery = battery
        self.vision_range = vision_range
        self.comm_range = comm_range
        
        self.carrying_object = False
        self.is_active = True
        self.is_connected = False
        self.nearby_agents = [] # List of tuples containing perceived positions of other agents
        
        self.role = None
        self.state = "EXPLORING" # Used by agents: EXPLORING, FETCHING, DELIVERING, EXITING, RENDEZVOUS
        
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
        if strategy.__class__.__name__ == "RandomTargetStrategy":
            self.role = "Scout"
        elif strategy.__class__.__name__ == "FrontierStrategy":
            self.role = "Collector"

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

    def sync_data(self, other):
        """
        Synchronizes map and object data with another agent efficiently using numpy and sets.
        This is called by the Simulation manager when agents are within comm_range.
        """
        if not self.is_active or not other.is_active:
            return
            
        # Merge local maps (takes the max, so it replaces -1 with known cell types)
        self.local_map = np.maximum(self.local_map, other.local_map)
        
        # Share known objects
        other.known_objects.update(self.known_objects)
        self.known_objects.update(other.known_objects)
        
        # If I am a Scout and I just shared my data with a Collector, I can clear my known_objects
        # so I stop the Rendezvous and go back to exploring.
        if self.role == "Scout" and other.role == "Collector":
            self.known_objects.clear()
        # Vice versa for the other agent if roles are reversed
        if other.role == "Scout" and self.role == "Collector":
            other.known_objects.clear()
            
        # Update last known metadata (position and role)
        self.last_known_others[other.id] = {"pos": other.pos, "role": other.role}

    def decide_and_move(self, env):
        if not self.is_active or self.battery <= 0:
            self.is_active = False
            return False # No move made
            
        next_pos = self.strategy.get_next_move(self, env)
        
        # Collision avoidance: do not move if the target cell is occupied by a known nearby agent
        if next_pos and next_pos in self.nearby_agents:
            # print(f"Agent {self.id} avoiding collision at {next_pos}.")
            next_pos = self.pos # Stay in place this tick
        
        if next_pos and next_pos != self.pos:
            self.pos = next_pos
            self.visited_cells[self.pos] = self.visited_cells.get(self.pos, 0) + 1
        elif next_pos != self.pos: # Only print stuck message if it actually tried to move but couldn't path
            print(f"Agent {self.id} stuck at {self.pos}. Strategy returned {next_pos}")
            
        # Picks up the object if he steps on it and has nothing in his hand, and is not a Scout
        if not self.carrying_object and env.has_object(self.pos) and self.role != "Scout":
            env.remove_object(self.pos)
            self.carrying_object = True
            self.state = "DELIVERING"
            if self.pos in self.known_objects:
                self.known_objects.remove(self.pos)
                
        # Drops off the object if it arrives at a warehouse entrance or internal cell
        # Warehouses have values 2 (internal), 3 (entrance), 4 (exit). Drop at 2 or 3.
        cell_type = env.get_cell_type(self.pos)
        if self.carrying_object and cell_type in [2, 3]:
            self.carrying_object = False
            self.state = "EXITING" # Immediately switch state to exit the warehouse
            
        # Resets state to EXPLORING if exiting the warehouse (stepped on 4 then out, or just wandering)
        if not self.carrying_object and self.state == "EXITING" and cell_type == 4:
            self.state = "EXPLORING" # Once on the exit, the next step will be out, so we can explore.
            
        self.battery -= 1
            
        if self.battery <= 0:
            self.is_active = False
            
        return True # Move/action made and costs 1 tick/energy
