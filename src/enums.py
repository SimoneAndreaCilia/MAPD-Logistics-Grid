from enum import Enum, IntEnum


class CellType(IntEnum):
    UNKNOWN   = -1
    CORRIDOR  =  0
    WALL      =  1
    WAREHOUSE =  2
    ENTRANCE  =  3
    EXIT      =  4


class AgentRole(str, Enum):
    SCOUT = "Scout"
    COLLECTOR = "Collector"
