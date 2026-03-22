from __future__ import annotations
import json
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .environment import Environment

def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def get_line_of_sight_cells(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> List[Tuple[int, int]]:
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

def has_line_of_sight(env: Environment, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
    """
    Check if there is Line of Sight (no walls in between) between pos1 and pos2.
    """
    cells = get_line_of_sight_cells(pos1, pos2)
    # Check only intermediate cells to allow "seeing" the target cell even if it is a wall
    for r, c in cells[1:-1]:
        if env.is_obstacle((r, c)):
            return False
    return True

def get_visible_cells(env: Environment, pos: Tuple[int, int], vision_range: int) -> List[Tuple[int, int]]:
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

@dataclass
class RewardSignal:
    """Broadcast signal from Simulation → Agents each tick."""
    current_tick: int
    max_ticks: int
    objects_collected: int
    objects_remaining: int
    current_score: int

    @property
    def time_pressure(self) -> float:
        """0.0 (start) → 1.0 (budget exhausted). Indicates temporal urgency."""
        if self.max_ticks == 0:
            return 1.0
        return self.current_tick / self.max_ticks

    @property
    def collection_ratio(self) -> float:
        """0.0 (none collected) → 1.0 (all collected). Measures mission progress."""
        total = self.objects_collected + self.objects_remaining
        if total == 0:
            return 1.0
        return self.objects_collected / total

    @property
    def urgency(self) -> float:
        """
        Combined signal: high urgency = time running out + objects still pending.
        Formula: time_pressure × (1 - collection_ratio)
        Range: 0.0 (no pressure) → 1.0 (max pressure)
        """
        return self.time_pressure * (1.0 - self.collection_ratio)


class SimulationLogger:
    def __init__(self):
        self.log_data = []
        
    def add_tick_state(self, tick: int, agents: List[Dict[str, Any]], score: int, objects_left: int) -> None:
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
        
    def save_log(self, filepath: str) -> None:
        with open(filepath, 'w') as f:
            json.dump(self.log_data, f, indent=2)
