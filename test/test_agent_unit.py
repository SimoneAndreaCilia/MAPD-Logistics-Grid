"""
Comprehensive unit tests for the Agent class logic. 
Covers synchronization, role-based handoffs, state machine transitions, 
and battery energy consumption.
"""
import os
import sys
import pytest
import numpy as np
from typing import Optional, Tuple

# Ensure src is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import Agent
from src.enums import AgentRole, AgentState, CellType
from src.environment import Environment
from src.strategies import BaseStrategy

# Mock Strategy that returns a specific move
class MockStrategy(BaseStrategy):
    def __init__(self, next_move=None):
        self.next_move = next_move
        
    def get_next_move(self, agent: 'Agent', env: 'Environment', targets: Optional[List[Tuple[int, int]]] = None) -> Optional[Tuple[int, int]]:
        return self.next_move

@pytest.fixture
def mock_env():
    class MockEnv:
        def __init__(self):
            self.objects = {(5, 5)}
            self.grid_size = 10
            self.cell_types = {}
            
        def has_object(self, pos):
            return pos in self.objects
            
        def remove_object(self, pos):
            if pos in self.objects:
                self.objects.remove(pos)
                
        def get_cell_type(self, pos):
            return self.cell_types.get(pos, CellType.CORRIDOR)
            
    return MockEnv()

def test_sync_maps_symmetric():
    """M6: Verify Agent.sync_maps(a, b) merges knowledge correctly and symmetrically."""
    a = Agent(agent_id=0, env_size=10, battery=500, vision_range=3, comm_range=5)
    b = Agent(agent_id=1, env_size=10, battery=500, vision_range=3, comm_range=5)
    
    # Give them different knowledge
    a.local_map[1, 1] = CellType.WALL
    b.local_map[2, 2] = CellType.WAREHOUSE
    
    a.known_objects.add((5, 5))
    b.known_objects.add((6, 6))
    
    # Atomic sync
    Agent.sync_maps(a, b)
    
    # Assert maps are identical and contain both discoveries
    assert np.array_equal(a.local_map, b.local_map)
    assert a.local_map[1, 1] == CellType.WALL
    assert a.local_map[2, 2] == CellType.WAREHOUSE
    
    # Assert objects are shared
    assert a.known_objects == b.known_objects
    assert (5, 5) in a.known_objects
    assert (6, 6) in a.known_objects

def test_scout_collector_handoff():
    """C2: Verify Scout clears known_objects after sync with a Collector."""
    scout = Agent(agent_id=0, env_size=10, battery=500, vision_range=3, comm_range=5, role=AgentRole.SCOUT)
    collector = Agent(agent_id=1, env_size=10, battery=500, vision_range=3, comm_range=5, role=AgentRole.COLLECTOR)
    
    scout.known_objects.add((5, 5))
    
    Agent.sync_maps(scout, collector)
    
    # Collector should have the object, Scout should have cleared its list
    assert (5, 5) in collector.known_objects
    assert len(scout.known_objects) == 0

def test_state_enum_usage():
    """M4: Verify Agent uses AgentState enum for its state."""
    agent = Agent(agent_id=0, env_size=10, battery=100, vision_range=3, comm_range=5)
    assert isinstance(agent.state, AgentState)
    assert agent.state == AgentState.EXPLORING
    
    agent.state = AgentState.FETCHING
    assert agent.state == AgentState.FETCHING

def test_validate_known_objects_prunes_stale(mock_env):
    """M2: Verify stale objects are removed from known_objects."""
    agent = Agent(agent_id=0, env_size=10, battery=100, vision_range=3, comm_range=5)
    agent.known_objects.add((5, 5)) # Active object
    agent.known_objects.add((6, 6)) # Stale/Ghost object
    
    agent.validate_known_objects(mock_env)
    
    assert (5, 5) in agent.known_objects
    assert (6, 6) not in agent.known_objects

def test_stuck_detection_with_none(mock_env, capsys):
    """C5: Verify that strategy returning None doesn't trigger false 'stuck' message."""
    agent = Agent(agent_id=0, env_size=10, battery=100, vision_range=3, comm_range=5)
    agent.set_strategy(MockStrategy(next_move=None))
    
    agent.decide_and_move(mock_env)
    
    captured = capsys.readouterr()
    assert "stuck" not in captured.out

def test_pickup_and_deliver_cycle(mock_env):
    """C3 & SRP: Verify the pickup-to-delivery lifecycle."""
    # Place agent on object
    agent = Agent(agent_id=0, env_size=10, battery=500, vision_range=3, comm_range=5, role=AgentRole.COLLECTOR)
    agent.pos = (5, 5)
    agent.set_strategy(MockStrategy(next_move=None))
    
    # 1. Pickup
    agent.decide_and_move(mock_env)
    assert agent.carrying_object is True
    assert agent.state == AgentState.DELIVERING
    assert (5, 5) not in mock_env.objects
    
    # 2. Move to Entrance
    mock_env.cell_types[(3, 3)] = CellType.ENTRANCE
    agent.pos = (3, 3)
    
    # 3. Delivery
    agent.decide_and_move(mock_env)
    assert agent.carrying_object is False
    assert agent.state == AgentState.EXITING

def test_battery_consumption(mock_env):
    """M7: Verify battery decreases through encapsulation properties."""
    agent = Agent(agent_id=0, env_size=10, battery=100, vision_range=3, comm_range=5)
    agent.set_strategy(MockStrategy(next_move=None))
    initial_battery = agent.battery
    
    agent.decide_and_move(mock_env)
    
    assert agent.battery == initial_battery - 1

def test_coordinator_strategic_position():
    """Verify CoordinatorRole finds central position and enters RELAYING state."""
    agent = Agent(agent_id=0, env_size=10, battery=100, vision_range=3, comm_range=5, role=AgentRole.COORDINATOR)
    
    # Mock environment to provide local_map layout
    # Center is (5, 5). We'll make only (4, 4) and (8, 8) as Corridors.
    agent.local_map[:, :] = CellType.WALL
    agent.local_map[4, 4] = CellType.CORRIDOR
    agent.local_map[8, 8] = CellType.CORRIDOR
    
    # Setup mock env
    class MockEnv:
        def has_object(self, *args): return False
        def remove_object(self, *args): pass
        def get_cell_type(self, *args): return CellType.CORRIDOR
        def is_passable(self, *args): return True
    env = MockEnv()
    
    # Create the role handler
    from src.roles import CoordinatorRole
    assert isinstance(agent.role_handler, CoordinatorRole)
    
    # First decision should target (4,4) as it's closer to center (5,5) than (8,8)
    # Manhattan distance (4,4) to (5,5) is 2. (8,8) to (5,5) is 6.
    targets = agent.role_handler.get_targets(agent, env)
    assert targets == [(4, 4)]
    
    # Manually move agent to target
    agent.pos = (4, 4)
    # Next decision should trigger RELAYING
    targets = agent.role_handler.get_targets(agent, env)
    assert targets == [(4, 4)]
    assert agent.state == AgentState.RELAYING

def test_coordinator_energy_saving():
    """Verify Agent doesn't consume battery when RELAYING."""
    agent = Agent(agent_id=0, env_size=10, battery=100, vision_range=3, comm_range=5, role=AgentRole.COORDINATOR)
    
    class MockEnv:
        def has_object(self, *args): return False
        def get_cell_type(self, *args): return CellType.CORRIDOR
        def is_passable(self, *args): return True
    env = MockEnv()
    
    agent.set_strategy(MockStrategy(next_move=(1, 1)))
    # Match the strategic position of the empty 10x10 grid center
    agent.pos = (5, 5) 
    agent.state = AgentState.RELAYING
    initial_battery = agent.battery
    
    agent.decide_and_move(env)
    
    # Since it's RELAYING:
    # 1. Position shouldn't change even if strategy says (1, 1)
    # 2. Battery shouldn't decrease
    assert agent.pos == (5, 5)
    assert agent.battery == initial_battery


if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__])
