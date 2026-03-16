import json
from .enums import CellType

class Warehouse:
    def __init__(self, w_id, side, entrance, exit_pos, area):
        self.id = w_id
        self.side = side
        self.entrance = tuple(entrance)
        self.exit = tuple(exit_pos)
        self.area = [tuple(c) for c in area]

class Environment:
    def __init__(self, json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        self.grid_size = data["metadata"]["grid_size"]
        self.grid = data["grid"]
        
        self.warehouses = []
        for w in data["warehouses"]:
            self.warehouses.append(Warehouse(
                w["id"], 
                w["side"], 
                w["entrance"], 
                w["exit"], 
                w["area"]
            ))
            
        # Ground truth of objects
        self.objects = [tuple(c) for c in data.get("objects", [])]

    def in_bounds(self, pos):
        r, c = pos
        return 0 <= r < self.grid_size and 0 <= c < self.grid_size

    def get_cell_type(self, pos):
        if not self.in_bounds(pos):
            return CellType.WALL
        r, c = pos
        return self.grid[r][c]

    def is_obstacle(self, pos):
        return self.get_cell_type(pos) in [CellType.WALL, CellType.WAREHOUSE]

    def is_passable(self, pos):
        return not self.is_obstacle(pos)


    def has_object(self, pos):
        return pos in self.objects

    def remove_object(self, pos):
        if pos in self.objects:
            self.objects.remove(pos)
            return True
        return False

    def get_ground_truth_objects(self):
        """Method used only by the simulation engine, forbidden to agents."""
        return self.objects.copy()
