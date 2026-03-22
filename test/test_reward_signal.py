"""
Unit tests for the RewardSignal mechanism.
Covers signal properties, agent integration, and simulation broadcast.
"""
import os
import sys
import pytest
import numpy as np

# Ensure src is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import RewardSignal
from src.agent import Agent
from src.enums import AgentRole, AgentState, CellType
from src.strategies import BaseStrategy


# ───────────────────────────────────────────────
# RewardSignal Properties
# ───────────────────────────────────────────────

def test_reward_signal_properties():
    """Verify time_pressure, collection_ratio, urgency for known values."""
    signal = RewardSignal(
        current_tick=250,
        max_ticks=500,
        objects_collected=3,
        objects_remaining=7,
        current_score=200
    )
    assert signal.time_pressure == pytest.approx(0.5)
    assert signal.collection_ratio == pytest.approx(0.3)
    # urgency = 0.5 * (1 - 0.3) = 0.5 * 0.7 = 0.35
    assert signal.urgency == pytest.approx(0.35)


def test_urgency_zero_at_start():
    """At tick=0, urgency must be 0.0 regardless of objects."""
    signal = RewardSignal(
        current_tick=0,
        max_ticks=500,
        objects_collected=0,
        objects_remaining=10,
        current_score=0
    )
    assert signal.time_pressure == pytest.approx(0.0)
    assert signal.urgency == pytest.approx(0.0)


def test_urgency_increases_over_time():
    """Urgency at tick=250 must be greater than at tick=50 (same objects)."""
    signal_early = RewardSignal(current_tick=50, max_ticks=500, objects_collected=0, objects_remaining=10, current_score=-50)
    signal_late = RewardSignal(current_tick=250, max_ticks=500, objects_collected=0, objects_remaining=10, current_score=-250)
    
    assert signal_late.urgency > signal_early.urgency


def test_urgency_decreases_with_collection():
    """With constant tick, collecting objects must reduce urgency."""
    signal_few = RewardSignal(current_tick=250, max_ticks=500, objects_collected=2, objects_remaining=8, current_score=0)
    signal_many = RewardSignal(current_tick=250, max_ticks=500, objects_collected=8, objects_remaining=2, current_score=0)
    
    assert signal_many.urgency < signal_few.urgency


def test_urgency_edge_case_all_collected():
    """If all objects are collected, urgency should be 0.0 regardless of time."""
    signal = RewardSignal(current_tick=499, max_ticks=500, objects_collected=10, objects_remaining=0, current_score=500)
    assert signal.collection_ratio == pytest.approx(1.0)
    assert signal.urgency == pytest.approx(0.0)


def test_urgency_edge_case_zero_max_ticks():
    """Edge case: max_ticks=0 should give time_pressure=1.0."""
    signal = RewardSignal(current_tick=0, max_ticks=0, objects_collected=0, objects_remaining=5, current_score=0)
    assert signal.time_pressure == pytest.approx(1.0)
    assert signal.urgency == pytest.approx(1.0)


# ───────────────────────────────────────────────
# Agent Integration
# ───────────────────────────────────────────────

def test_agent_receives_signal():
    """After update_reward_signal(), agent.urgency must reflect the signal."""
    agent = Agent(agent_id=0, env_size=10, battery=500, vision_range=3, comm_range=5)
    signal = RewardSignal(current_tick=250, max_ticks=500, objects_collected=3, objects_remaining=7, current_score=50)
    
    agent.update_reward_signal(signal)
    
    assert agent.reward_signal is not None
    assert agent.urgency == pytest.approx(0.35)


def test_agent_default_urgency_zero():
    """Without any signal, agent.urgency must be 0.0 (retrocompatibility)."""
    agent = Agent(agent_id=0, env_size=10, battery=500, vision_range=3, comm_range=5)
    assert agent.urgency == pytest.approx(0.0)


# ───────────────────────────────────────────────
# Simulation Broadcast
# ───────────────────────────────────────────────

def test_simulation_broadcasts_signal():
    """After sim.step(), all active agents must have a non-None reward_signal."""
    from src.environment import Environment
    from src.simulation import Simulation
    from src.strategies import FrontierStrategy
    
    # Use a real environment file
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_path, "data", "A.json")
    
    if not os.path.exists(env_path):
        pytest.skip("Environment file A.json not found")
    
    env = Environment(env_path)
    agents = []
    for i in range(2):
        agent = Agent(agent_id=i, env_size=env.grid_size, battery=500, vision_range=3, comm_range=2, role=AgentRole.SCOUT)
        agent.set_strategy(FrontierStrategy(), name="Frontier")
        agents.append(agent)
    
    sim = Simulation(env, agents, max_ticks=50)
    
    # Before any step, reward_signal should be None
    assert all(a.reward_signal is None for a in agents)
    
    # Run one step
    sim.step()
    
    # After step, active agents should have received the signal
    active_agents = [a for a in agents if a.is_active]
    assert len(active_agents) > 0
    for agent in active_agents:
        assert agent.reward_signal is not None
        assert agent.reward_signal.max_ticks == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
