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
    COORDINATOR = "Coordinator"

class AgentState(str, Enum):
    EXPLORING  = "EXPLORING"
    FETCHING   = "FETCHING"
    DELIVERING = "DELIVERING"
    EXITING    = "EXITING"
    RENDEZVOUS = "RENDEZVOUS"
    RETURNING  = "RETURNING"
    PARKED     = "PARKED"
    RELAYING   = "RELAYING"
