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

        # 0 & 1. Need to return to warehouse? (Low battery OR Carrying object)
        is_low_battery = agent.battery <= BATTERY_LOW_THRESHOLD and agent.state != AgentState.PARKED
        
        if is_low_battery or agent.carrying_object:
            warehouse_entrances = set(zip(*np.where(agent.local_map == CellType.ENTRANCE)))
            if warehouse_entrances:
                agent.state = AgentState.DELIVERING if agent.carrying_object else AgentState.RETURNING
                return list(warehouse_entrances)
            else:
                agent.state = AgentState.EXPLORING

        # 1.5. Inside a warehouse without an object? Head out!
        elif agent.local_map[agent.pos] in [CellType.WAREHOUSE, CellType.ENTRANCE, CellType.EXIT]:
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
            
            agent.state = AgentState.EXPLORING

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
        from .config import BATTERY_LOW_THRESHOLD

        # If carrying an object or low battery, fetching is strictly disabled.
        # This prevents falling back into fetching if the warehouse is unknown and the agent is exploring.
        if agent.carrying_object or (agent.battery <= BATTERY_LOW_THRESHOLD and agent.state != AgentState.PARKED):
            return None

        # Knows objects? Go to the nearest one
        if agent.known_objects:
            agent.state = AgentState.FETCHING
            return list(agent.known_objects)
        return None


class CoordinatorRole(BaseRole):
    def __init__(self):
        super().__init__()
        self.strategic_pos = None

    def get_role_specific_targets(self, agent: 'Agent', env: 'Environment') -> Optional[List[Tuple[int, int]]]:
        # 1. Calculate strategic position
        if self.strategic_pos is None or agent.local_map[self.strategic_pos] == CellType.WALL:
            h, w = agent.local_map.shape
            center = (h // 2, w // 2)
            
            # Consider both explored corridors and unknown cells as valid candidates for the center
            valid_mask = (agent.local_map == CellType.CORRIDOR) | (agent.local_map == CellType.UNKNOWN)
            candidates = list(zip(*np.where(valid_mask)))
                
            if candidates:
                self.strategic_pos = min(candidates, key=lambda pos: abs(pos[0]-center[0]) + abs(pos[1]-center[1]))

        # 2. Reached position? Stasis mode.
        if self.strategic_pos:
            if agent.pos == self.strategic_pos:
                agent.state = AgentState.RELAYING
                return [agent.pos]
            else:
                agent.state = AgentState.EXPLORING
                return [self.strategic_pos]
                
        return None
