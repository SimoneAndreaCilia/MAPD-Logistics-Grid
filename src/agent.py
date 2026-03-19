from __future__ import annotations
import numpy as np
from typing import Tuple, List, Set, Dict, Optional, Any, TYPE_CHECKING
from .enums import AgentRole, CellType, AgentState
from .utils import get_visible_cells, manhattan_distance

from .roles import ScoutRole, CollectorRole, BaseRole

if TYPE_CHECKING:
    from .environment import Environment
    from .strategies import BaseStrategy
    from .enums import AgentRole

ROLE_REGISTRY = {
    AgentRole.SCOUT: ScoutRole,
    AgentRole.COLLECTOR: CollectorRole,
}

class Agent:
    def __init__(
        self, 
        agent_id: int, 
        env_size: int, 
        battery: int, 
        vision_range: int, 
        comm_range: int, 
        role: Optional[AgentRole] = None
    ):
        self.id: int = agent_id
        self.pos: Tuple[int, int] = (0, 0)
        self._role: Optional[AgentRole] = role
        role_class = ROLE_REGISTRY.get(role, BaseRole)
        self.role_handler = role_class()

        self._state: AgentState = AgentState.EXPLORING 
        self._battery: int = battery
        self.vision_range: int = vision_range
        self.comm_range: int = comm_range
        
        self.carrying_object: bool = False
        self.is_active: bool = True
        self.is_connected: bool = False
        self.nearby_agents: List[Tuple[int, int]] = [] 
        
        # Local map: -1 indicates 'unknown'
        self.local_map: np.ndarray = np.full((env_size, env_size), -1, dtype=int)
        # The starting cell is always a free corridor
        self.local_map[0, 0] = CellType.CORRIDOR 
        
        # Set of coordinates of objects seen but not yet collected
        self.known_objects: Set[Tuple[int, int]] = set()
        
        # Track number of visits to each cell to avoid getting stuck
        self.visited_cells: Dict[Tuple[int, int], int] = {self.pos: 1}
        self.last_pos: Optional[Tuple[int, int]] = None
        self.current_target: Optional[Tuple[int, int]] = None 
        
        # Track last known positions of other agents to coordinate map sharing
        self.last_known_others: Dict[int, Dict[str, Any]] = {}
        
        self.strategy: Optional[BaseStrategy] = None

    def set_strategy(self, strategy: BaseStrategy) -> None:
        self.strategy = strategy

    @property
    def state(self) -> AgentState:
        return self._state

    @state.setter
    def state(self, value: AgentState) -> None:
        self._state = value

    @property
    def role(self) -> AgentRole:
        return self._role

    @property
    def battery(self) -> int:
        return self._battery

    def __repr__(self) -> str:
        return (
            f"Agent(id={self.id}, pos={self.pos}, "
            f"battery={self._battery}, role={self._role.value if self._role else 'None'}, "
            f"state={self._state.value})"
        )

    def sense(self, env: Environment) -> None:
        if not self.is_active:
            return
            
        visible_cells = get_visible_cells(env, self.pos, self.vision_range)
        for r, c in visible_cells:
            # Update the map with the cell type
            self.local_map[r, c] = env.get_cell_type((r, c))
            
            # If it detects an object on the cell, it adds it to the known objects
            if env.has_object((r, c)) and not self.carrying_object:
                self.known_objects.add((r, c))

    @staticmethod
    def sync_maps(a: Agent, b: Agent) -> None:
        """
        Symmetrically synchronizes map and object data between two agents in a single call.
        Both agents get the merged result atomically, avoiding the double-call mutation bug.
        This is called by the Simulation manager when agents are within comm_range.
        """
        if not a.is_active or not b.is_active:
            return

        # Merge local maps symmetrically: both agents receive the best-known value per cell
        merged_map = np.maximum(a.local_map, b.local_map)
        a.local_map = merged_map
        b.local_map = merged_map.copy()

        # Compute the union of known objects BEFORE any handoff clearing
        shared_objects = a.known_objects | b.known_objects
        a.known_objects = shared_objects.copy()
        b.known_objects = shared_objects.copy()

        # Scout → Collector handoff: once objects are shared, the Scout clears its list
        # so it exits RENDEZVOUS and goes back to exploring.
        if a.role == AgentRole.SCOUT and b.role == AgentRole.COLLECTOR:
            a.known_objects.clear()
        elif b.role == AgentRole.SCOUT and a.role == AgentRole.COLLECTOR:
            b.known_objects.clear()

        # Update each agent's last-known metadata about the other
        a.last_known_others[b.id] = {"pos": b.pos, "role": b.role, "target": b.current_target}
        b.last_known_others[a.id] = {"pos": a.pos, "role": a.role, "target": a.current_target}

    def decide_and_move(self, env: Environment) -> bool:
        """
        Orchestrates one agent tick: guard → strategy → move → pickup → deliver → state → energy.
        Returns True if a tick was consumed, False if the agent is inactive.
        """
        if not self.is_active or self.battery <= 0:
            self.is_active = False
            return False

        targets = self.role_handler.get_targets(self, env)
        next_pos = self.strategy.get_next_move(self, env, targets)

        # Target management: clear target if already reached
        if self.current_target == self.pos:
            self.current_target = None

        self._move_to(next_pos, env)
        self._try_pickup(env)
        self._try_deliver(env)
        self._try_park(env)
        self._update_state(env)
        self._consume_energy()

        return True

    # ------------------------------------------------------------------
    # Private helpers — each with a single, well-defined responsibility
    # ------------------------------------------------------------------

    def _move_to(self, next_pos: Optional[Tuple[int, int]], env: Environment) -> None:
        """Updates the agent's position if next_pos is valid, passable, and different from the current one."""
        if next_pos and next_pos != self.pos and env.is_passable(next_pos):
            self.last_pos = self.pos
            self.pos = next_pos
            self.visited_cells[self.pos] = self.visited_cells.get(self.pos, 0) + 1
        elif next_pos is not None and next_pos != self.pos:
            # Strategy returned a position but pathfinding failed to reach it
            print(f"Agent {self.id} stuck at {self.pos}. Strategy returned {next_pos}")
            self.current_target = None

    def _try_pickup(self, env: Environment) -> None:
        """Picks up an object if the agent is standing on one, is idle, and is not a Scout."""
        if not self.carrying_object and env.has_object(self.pos) and self.role != AgentRole.SCOUT:
            env.remove_object(self.pos)
            self.carrying_object = True
            self.state = AgentState.DELIVERING
            self.known_objects.discard(self.pos)  # discard is safe even if not present

    def _try_deliver(self, env: Environment) -> None:
        """Drops off the carried object if the agent is inside a warehouse (entrance or internal cell)."""
        if self.carrying_object and env.get_cell_type(self.pos) in [CellType.WAREHOUSE, CellType.ENTRANCE]:
            self.carrying_object = False
            from .config import BATTERY_LOW_THRESHOLD
            if self.battery <= BATTERY_LOW_THRESHOLD:
                self.state = AgentState.RETURNING
            else:
                self.state = AgentState.EXITING  # Immediately switch state to exit the warehouse

    def _try_park(self, env: Environment) -> None:
        """Parks the agent if its battery is low and it is inside a warehouse."""
        from .config import BATTERY_LOW_THRESHOLD
        if self.battery <= BATTERY_LOW_THRESHOLD and env.get_cell_type(self.pos) in [CellType.WAREHOUSE, CellType.ENTRANCE]:
            self.is_active = False
            self.state = AgentState.PARKED

    def _update_state(self, env: Environment) -> None:
        """
        Manages FSM state transitions.
        Resets to EXPLORING only when back in a corridor, ensuring the agent
        follows the EXITING path through the exit cell (type 4) before exploring again.
        """
        cell_type = env.get_cell_type(self.pos)
        if not self.carrying_object and self.state in [AgentState.EXITING, AgentState.DELIVERING, AgentState.FETCHING] and cell_type == CellType.CORRIDOR:
            self.state = AgentState.EXPLORING
            self.current_target = None  # Forces re-selection of exploration target

    def _consume_energy(self) -> None:
        """Decrements battery by 1 and deactivates the agent if it reaches zero."""
        self._battery -= 1
        if self._battery <= 0:
            self.is_active = False

    def validate_known_objects(self, env: Environment) -> None:
        """Removes objects from known_objects if they are no longer present in the environment (e.g., collected by another agent)."""
        self.known_objects = {pos for pos in self.known_objects if env.has_object(pos)}

