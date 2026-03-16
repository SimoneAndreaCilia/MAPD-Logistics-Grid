import json
from typing import List, Tuple
from .enums import CellType

class Warehouse:
    def __init__(self, w_id: int, side: str, entrance: List[int], exit_pos: List[int], area: List[List[int]]):
        self.id: int = w_id
        self.side: str = side
        self.entrance: Tuple[int, int] = tuple(entrance)  # type: ignore
        self.exit: Tuple[int, int] = tuple(exit_pos)  # type: ignore
        self.area: List[Tuple[int, int]] = [tuple(c) for c in area]  # type: ignore

class Environment:
    def __init__(self, json_path: str):
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

    def in_bounds(self, pos: Tuple[int, int]) -> bool:
        r, c = pos
        return 0 <= r < self.grid_size and 0 <= c < self.grid_size

    def get_cell_type(self, pos: Tuple[int, int]) -> int:
        if not self.in_bounds(pos):
            return CellType.WALL
        r, c = pos
        return self.grid[r][c]

    def is_obstacle(self, pos: Tuple[int, int]) -> bool:
        return self.get_cell_type(pos) in [CellType.WALL, CellType.WAREHOUSE]

    def is_passable(self, pos: Tuple[int, int]) -> bool:
        return not self.is_obstacle(pos)


    def has_object(self, pos: Tuple[int, int]) -> bool:
        return pos in self.objects

    def remove_object(self, pos: Tuple[int, int]) -> bool:
        if pos in self.objects:
            self.objects.remove(pos)
            return True
        return False

    def get_ground_truth_objects(self) -> List[Tuple[int, int]]:
        """Method used only by the simulation engine, forbidden to agents."""
        return self.objects.copy()
