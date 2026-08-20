"""
Script python that allow us to generate problem file in pddl+
"""
import re
import os
import logging
import sys

# Defining the pattern to catch occupancy rows
# \(\= search for (=
# \s* or \s+ for optional spaces
# ([a-zA-Z0-9_]+) for the location name
# ([0-9.]+) for the occupancy value
occupancy_pattern = re.compile(r"\(\=\s*\(occupancy\s+([a-zA-Z0-9_]+)\)\s+([0-9.]+)\)")
capacity_pattern = re.compile(r"\(\=\s*\(capacity\s+([a-zA-Z0-9_]+)\)\s+([0-9.]+)\)")
turn_rate_pattern = re.compile(r"\(\=\s*\(turnrate\s+([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_]+)\)\s+([0-9.]+)\)")

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

class TurnRate:
    def __init__(self, stage, origin, destination, value):
        self.stage = stage
        self.origin = origin
        self.destination = destination
        self.value = value

"""
Read pddl+ file and extract traffic and topology data
"""
def parse_pddl_file(file_path):

    occupancies = {}
    capacity = {}
    turn_rate = []

    log.info(f"Opening pddl+ file: {file_path}")

    with open(file_path, "r") as file:
        for line in file:
            occupancy_match = occupancy_pattern.search(line)
            capacity_match = capacity_pattern.search(line)
            turn_rate_match = turn_rate_pattern.search(line)
            if occupancy_match:
                link_name = occupancy_match.group(1)
                occupancy_value = float(occupancy_match.group(2))
                occupancies[link_name] = occupancy_value
            elif capacity_match:
                link_name = capacity_match.group(1)
                capacity_value = float(capacity_match.group(2))
                capacity[link_name] = capacity_value
            elif turn_rate_match:
                stage = turn_rate_match.group(1)
                origin = turn_rate_match.group(2)
                destination = turn_rate_match.group(3)
                turn_rate_value = float(turn_rate_match.group(4))
                turn_rate.append(TurnRate(stage, origin, destination, turn_rate_value))

    log.info(f"Extracted {len(occupancies)} occupancies, {len(capacity)} capacities, and {len(turn_rate)} turn rates from the pddl+ file.")
    return occupancies, capacity, turn_rate

if __name__ == "__main__":
    # 1. Trova dinamicamente la cartella esatta in cui si trova questo script (pddl_parser.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Costruisci il percorso unendo le cartelle (torna indietro di 2 livelli da src/parser/ e poi entra in data)
    # script_dir = src/parser -> .. = src -> .. = root del progetto -> data/base_instances/...
    file_path = os.path.abspath(os.path.join(script_dir, "..", "..", "data", "base_instances", "p01[count=350].pddl"))

    parse_pddl_file(file_path)
