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

"""
Increase occupancy based on stress_factor
Apply clipping thought static_capacity
"""
def apply_occupancy_stress(occupancies, capacities, stress_factor):
    log.info(f"Applying stress factor {stress_factor} to occupancies.")
    stressed_occupancies = {}

    for link_name, current_occupancy in occupancies.items():
        # calculating new theoretical value
        new_occupancy = current_occupancy * stress_factor

        max_cap = capacities.get(link_name, float("inf"))

        if new_occupancy <= max_cap:
            stressed_occupancies[link_name] = new_occupancy
        else:
            stressed_occupancies[link_name] = max_cap

    return stressed_occupancies

"""
    Raggruppa i turn rates per (stage, origin) e applica uno sbilanciamento
    garantendo che la somma delle probabilità rimanga 1.0.
"""
def apply_turn_rate_stress(turn_rates, stress_factor):

    log.info(f"Applicazione stress test sui Turn Rates...")

    # 1. Creiamo un dizionario per raggruppare le direzioni
    # La chiave sarà una tupla: (stage, origin)
    # Il valore sarà una lista di oggetti TurnRate
    grouped_rates = {}

    for tr in turn_rates:
        key = (tr.stage, tr.origin)
        if key not in grouped_rates:
            grouped_rates[key] = []
        grouped_rates[key].append(tr)

    stressed_turn_rates = []
    for key, rates in grouped_rates.items():
        if len(rates) == 1:
            stressed_turn_rates.append(rates[0])
            continue

        # Turn rate with the highest value
        max_route = max(rates, key=lambda r: r.value)
        # other routes
        other_routes = [r for r in rates if r != max_route]

        stressed_max_value = min(max_route.value * stress_factor, 1.0)
        delta = stressed_max_value - max_route.value

        # sum other routes probability
        sum_others = sum(tr.value for tr in other_routes)

        # sub the delta from other routes
        if sum_others > 0:
            for tr in other_routes:
                tr.value = tr.value - (delta * (tr.value / sum_others))
                tr.value = max(0.0, tr.value)

        max_route.value = stressed_max_value

        stressed_turn_rates.append(max_route)
        stressed_turn_rates.extend(other_routes)

    return stressed_turn_rates

def generate_pddl_file(file_path, stress_factor=1.2):
    log.info(f"Generating pddl+ file: {file_path}")

    occupancies, capacity, turn_rate = parse_pddl_file(file_path)
    stressed_occupancies = apply_occupancy_stress(occupancies, capacity, stress_factor)
    stressed_turn_rates = apply_turn_rate_stress(turn_rate, stress_factor)

    turn_rate_dict = {
        (tr.stage, tr.origin, tr.destination): tr.value
        for tr in stressed_turn_rates
    }

    # 3. Creazione del percorso di Output
    # Es: da "data/base_instances/p01.pddl" a "data/generated_instances/p01_stressed.pddl"
    base_name = os.path.basename(file_path)
    name_without_ext, ext = os.path.splitext(base_name)
    new_filename = f"{name_without_ext}_stressed{ext}"

    # Assumiamo che generated_instances sia allo stesso livello di base_instances
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.abspath(os.path.join(script_dir, "..", "..", "data", "generated_instances", new_filename))

    log.info(f"Writing new file in: {output_path}")

    # 4. Sostituzione e Scrittura
    with open(file_path, "r") as f_in, open(output_path, "w") as f_out:
        for line in f_in:
            occupancy_match = occupancy_pattern.search(line)
            turn_rate_match = turn_rate_pattern.search(line)

            # Cerca se la riga attuale è un'occupancy (usando occupancy_pattern)
            # Se lo è, estrai il nome del link, cerca il nuovo valore in stressed_occupancies
            # E ricrea la riga testuale con il nuovo valore.
            if occupancy_match:
                stressed_link_name = occupancy_match.group(1)
                if stressed_link_name in stressed_occupancies:
                    new_value = stressed_occupancies[stressed_link_name]
                    new_line = f"(= (occupancy {stressed_link_name}) {new_value})\n"
                    f_out.write(new_line)
                    continue
            elif turn_rate_match:
                stage = turn_rate_match.group(1)
                origin = turn_rate_match.group(2)
                destination = turn_rate_match.group(3)

                key = (stage, origin, destination)
                if key in turn_rate_dict:
                    new_turn_rate_value = turn_rate_dict[key]
                    new_line = f"(= (turnrate {stage} {origin} {destination}) {new_turn_rate_value})\n"
                    f_out.write(new_line)
                    continue
            f_out.write(line)

    log.info("Generated pddl file")

def generate_pddl_concert_scenario_file(file_path, stress_factor=1.2):
    log.info(f"Generating pddl+ file: {file_path}")

    occupancies, capacity, turn_rate = parse_pddl_file(file_path)
    stressed_occupancies = apply_occupancy_stress(occupancies, capacity, stress_factor)
    stressed_turn_rates = apply_concert_turnrate(turn_rate, target_destination="hsac3_c_wrac1", boost_value=0.8)

    turn_rate_dict = {
        (tr.stage, tr.origin, tr.destination): tr.value
        for tr in stressed_turn_rates
    }

    # 3. Creazione del percorso di Output
    # Es: da "data/base_instances/p01.pddl" a "data/generated_instances/p01_stressed.pddl"
    base_name = os.path.basename(file_path)
    name_without_ext, ext = os.path.splitext(base_name)
    new_filename = f"{name_without_ext}_concert_scenario{ext}"

    # Assumiamo che generated_instances sia allo stesso livello di base_instances
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.abspath(os.path.join(script_dir, "..", "..", "data", "generated_instances", new_filename))

    log.info(f"Writing new file in: {output_path}")

    # 4. Sostituzione e Scrittura
    with open(file_path, "r") as f_in, open(output_path, "w") as f_out:
        for line in f_in:
            occupancy_match = occupancy_pattern.search(line)
            turn_rate_match = turn_rate_pattern.search(line)

            # Cerca se la riga attuale è un'occupancy (usando occupancy_pattern)
            # Se lo è, estrai il nome del link, cerca il nuovo valore in stressed_occupancies
            # E ricrea la riga testuale con il nuovo valore.
            if occupancy_match:
                stressed_link_name = occupancy_match.group(1)
                if stressed_link_name in stressed_occupancies:
                    new_value = stressed_occupancies[stressed_link_name]
                    new_line = f"(= (occupancy {stressed_link_name}) {new_value})\n"
                    f_out.write(new_line)
                    continue
            elif turn_rate_match:
                stage = turn_rate_match.group(1)
                origin = turn_rate_match.group(2)
                destination = turn_rate_match.group(3)

                key = (stage, origin, destination)
                if key in turn_rate_dict:
                    new_turn_rate_value = turn_rate_dict[key]
                    new_line = f"(= (turnrate {stage} {origin} {destination}) {new_turn_rate_value})\n"
                    f_out.write(new_line)
                    continue
            f_out.write(line)

    log.info("Concert scenario successfully generated!")


def apply_concert_turnrate(turn_rates, target_destination, boost_value=0.8):
    log.info(f"Generating Concert Scenario: traffic diversion towards {target_destination} al {boost_value * 100}%")

    # 1. Filtriamo SOLO i turn rate in ingresso dall'esterno (Onda Anomala)
    outside_rates = [tr for tr in turn_rates if tr.stage == "fake" and tr.origin == "outside"]

    # 2. Troviamo la rotta del concerto e le rotte secondarie
    concert_route = None
    other_routes = []
    const_probability = 1.0

    for tr in outside_rates:
        if tr.destination == target_destination:
            concert_route = tr
        else:
            other_routes.append(tr)

    if not concert_route:
        log.error(f"Destination not found {target_destination} in boundary links!")
        return []


    # Imposta direttamente il valore della concert_route uguale al boost_value
    concert_route.value = boost_value

    # Calcola quanta probabilità rimane per tutte le altre strade (1.0 - boost_value)
    remaining_prob =  const_probability - boost_value

    # Calcola la somma delle vecchie probabilità delle altre strade (ci serve per le proporzioni)
    sum_others =  sum(tr.value for tr in other_routes)

    # Ricalcola il valore delle rotte secondarie con un ciclo for.
    if sum_others > 0:
        for tr in other_routes:
            # Formula matematica: nuovo_valore = (vecchio_valore / somma_altri) * probabilita_rimanente
            tr.value = (tr.value / sum_others) * remaining_prob


    # Alla fine raccogliamo le rotte modificate per restituirle
    modified_rates = [concert_route]
    modified_rates.extend(other_routes)

    return modified_rates

if __name__ == "__main__":
    # 1. Trova dinamicamente la cartella esatta in cui si trova questo script (pddl_parser.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Costruisci il percorso unendo le cartelle (torna indietro di 2 livelli da src/parser/ e poi entra in data)
    # script_dir = src/parser -> .. = src -> .. = root del progetto -> data/base_instances/...
    for i in range(1,6):
        path_file = f"p0{i}[count=350].pddl"
        file_path = os.path.abspath(
            os.path.join(script_dir, "..", "..", "data", "base_instances", path_file))
        generate_pddl_file(file_path, stress_factor=1.2)
        generate_pddl_concert_scenario_file(file_path, stress_factor=1.2)


