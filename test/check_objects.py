"""
This script verifies the initial state of the environment by printing 
the coordinates and cell types for all objects defined in the JSON map.
"""
from src.environment import Environment
import os

env = Environment("data/A.json")
objects = env.objects
print("Object locations and types:")
for obj in objects:
    cell_type = env.get_cell_type(obj)
    print(f"Pos {obj}: Type {cell_type}")
