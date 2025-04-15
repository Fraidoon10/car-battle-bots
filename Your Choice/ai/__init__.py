# CombinedChaseHideGame/ai/__init__.py
# --- START OF FILE __init__.py ---

# Make AI components easily importable from the 'ai' package
from .fsm import FSM, DefenseState
from .pathfinding import AStar
from .prediction import PositionPredictor

__all__ = [
    'FSM',
    'DefenseState',
    'AStar',
    'PositionPredictor'
]

# --- END OF FILE __init__.py ---