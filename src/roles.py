from typing import List, Tuple, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from .agent import Agent
    from .environment import Environment

from .enums import AgentRole, CellType, AgentState

class BaseRole:
    def __init__(self):
        pass

    def get_targets(self, agent: 'Agent', env: 'Environment') -> Optional[List[Tuple[int, int]]]:
        """
        Evaluates the environment and standard agent state (battery, carrying status)
        to determine the required target cells. Updates agent.state accordingly.
        Returns a list of potential targets or None if exploration is needed.
        """
        from .config import BATTERY_LOW_THRESHOLD

        # 0. Low Battery? Return to warehouse entrance
        if agent.battery <= BATTERY_LOW_THRESHOLD and agent.state != AgentState.PARKED and not agent.carrying_object:
            agent.state = AgentState.RETURNING
            warehouse_entrances = set(zip(*np.where(agent.local_map == CellType.ENTRANCE)))
            if warehouse_entrances:
                return list(warehouse_entrances)
            return None

        # 1. Carrying an object? Return to warehouse ENTRANCE
        if agent.carrying_object:
            agent.state = AgentState.DELIVERING
            warehouse_entrances = set(zip(*np.where(agent.local_map == CellType.ENTRANCE)))
            if warehouse_entrances:
                return list(warehouse_entrances)
            return None

        # 1.5. Inside a warehouse without an object? Head out!
        if not agent.carrying_object and agent.local_map[agent.pos] in [CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT]:
            if agent.state == AgentState.RETURNING:
                return None  # Stay inside and wait to be parked

            agent.state = AgentState.EXITING
            current_type = agent.local_map[agent.pos]

            if current_type == CellType.EXIT:
                corridors = set(zip(*np.where(agent.local_map == CellType.CORRIDOR)))
                if corridors:
                    return list(corridors)
            else:
                warehouse_exits = set(zip(*np.where(agent.local_map == CellType.EXIT)))
                if warehouse_exits:
                    return list(warehouse_exits)
                else:
                    corridors = set(zip(*np.where(agent.local_map == CellType.CORRIDOR)))
                    if corridors:
                        return list(corridors)
            return None

        # 2. Base role has no special logic unless overridden, check specific role logic
        targets = self.get_role_specific_targets(agent, env)
        if targets:
            return targets
        
        # 3. No targets, start exploring
        agent.state = AgentState.EXPLORING
        return None

    def get_role_specific_targets(self, agent: 'Agent', env: 'Environment') -> Optional[List[Tuple[int, int]]]:
        """Override in subclasses to provide role specific targets."""
        return None


class ScoutRole(BaseRole):
    def get_role_specific_targets(self, agent: 'Agent', env: 'Environment') -> Optional[List[Tuple[int, int]]]:
        # Scout knows objects? RENDEZVOUS with nearest Collector to share data
        if agent.known_objects:
            collectors = [info for info in agent.last_known_others.values() if info.get("role") == AgentRole.COLLECTOR]
            if collectors:
                agent.state = AgentState.RENDEZVOUS
                collector_positions = [c["pos"] for c in collectors]
                nearest_collector_pos = min(collector_positions, key=lambda p: abs(p[0]-agent.pos[0]) + abs(p[1]-agent.pos[1]))
                return [nearest_collector_pos]
        return None


class CollectorRole(BaseRole):
    def get_role_specific_targets(self, agent: 'Agent', env: 'Environment') -> Optional[List[Tuple[int, int]]]:
        # Knows objects? Go to the nearest one
        if agent.known_objects:
            agent.state = AgentState.FETCHING
            return list(agent.known_objects)
        return None
