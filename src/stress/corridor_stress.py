"""
Script python per generare lo scenario 'ondata in ingresso' (Scenario 1).

Stressa SOLO l'occupancy del link boundary che alimenta l'inizio del
corridoio, scelto tramite un'euristica a un hop (fake->outside->X, poi
X->primo_link_corridoio). Non tocca i turnrate (comportamento dei
guidatori, non oggetto di stress) e non tocca il blocco :goal, che resta
quello originale del file p0i passato in input.

Dipende dal project_parser esistente (parse_pddl_file, TurnRate, occupancy_pattern)
definito in src/project_parser/pddl_parser.py.
"""
import os
import logging
import sys
import project_parser.pddl_parser as pddl_parser

# Import dal modulo project_parser esistente (stessa cartella /src, sottocartella project_parser)
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project_parser"))

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def trova_link_ingresso_corridoio(turn_rates, primo_link_corridoio):
    """
    Sceglie, tra i link boundary (stage='fake', origin='outside'), quello
    con il punteggio piu' alto verso il primo link del corridoio.

    score(X) = turnrate(fake, outside, X) * max_stage[turnrate(stage, X, primo_link_corridoio)]

    Controllo a UN SOLO HOP: non si propaga la verifica oltre il primo
    link del corridoio, la propagazione successiva e' responsabilita'
    del modello PDDL+ / del planner, non di questa euristica.
    """
    log.info(f"Ricerca del link boundary che alimenta {primo_link_corridoio}...")

    candidati_boundary = [tr for tr in turn_rates if tr.stage == "fake" and tr.origin == "outside"]

    migliore_link = None
    migliore_score = 0.0

    for tr_boundary in candidati_boundary:
        link_x = tr_boundary.destination

        # turnrate interni che partono da link_x e vanno verso il primo link del corridoio,
        # in una qualsiasi stage (non sappiamo/non ci interessa quando sara' attiva)
        turnrate_verso_corridoio = [
            tr.value for tr in turn_rates
            if tr.origin == link_x and tr.destination == primo_link_corridoio
        ]

        if not turnrate_verso_corridoio:
            continue  # link_x non porta affatto verso il corridoio, scartalo

        best_interno = max(turnrate_verso_corridoio)
        score = tr_boundary.value * best_interno

        log.info(f"  Candidato {link_x}: turnrate_ingresso={tr_boundary.value}, "
                 f"turnrate_verso_corridoio={best_interno}, score={score:.4f}")

        if score > migliore_score:
            migliore_score = score
            migliore_link = link_x

    if migliore_link is None:
        log.error(f"Nessun link boundary trovato che porti verso {primo_link_corridoio}")
        return None

    log.info(f"Link scelto per lo stress in ingresso: {migliore_link} (score={migliore_score:.4f})")
    return migliore_link



def generate_corridor_inflow_scenario(file_path, primo_link_corridoio, boost_factor=1.5):
    """
    Genera lo scenario 'ondata in ingresso' a partire da un'istanza p0i
    GIA' COMPLETA (goal incluso, es. p05). Modifica SOLO l'occupancy del
    link boundary scelto dall'euristica. Il resto del file (incluso il
    blocco :goal) resta invariato.
    """
    log.info(f"Generazione scenario corridor inflow per: {file_path}")

    occupancies, capacities, turn_rates = pddl_parser.parse_pddl_file(file_path)

    link_target = trova_link_ingresso_corridoio(turn_rates, primo_link_corridoio)
    if link_target is None:
        log.error("Impossibile generare lo scenario: nessun link valido trovato.")
        return None

    if link_target not in occupancies:
        log.error(f"Il link scelto {link_target} non ha una occupancy definita nel file.")
        return None

    occupancy_corrente = occupancies[link_target]
    max_cap = capacities.get(link_target, float("inf"))

    nuova_occupancy = min(occupancy_corrente * boost_factor, max_cap)
    log.info(f"Occupancy di {link_target}: {occupancy_corrente} -> {nuova_occupancy} "
             f"(boost_factor={boost_factor}, clipping su capacity={max_cap})")

    # Costruzione percorso di output, stesso pattern delle funzioni esistenti
    base_name = os.path.basename(file_path)
    name_without_ext, ext = os.path.splitext(base_name)
    new_filename = f"{name_without_ext}_corridor_inflow{ext}"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.abspath(
        os.path.join(script_dir, "..", "..", "data", "generated_instances", new_filename))

    log.info(f"Scrittura nuovo file in: {output_path}")

    with open(file_path, "r") as f_in, open(output_path, "w") as f_out:
        for line in f_in:
            occupancy_match = pddl_parser.occupancy_pattern.search(line)

            if occupancy_match:
                link_name = occupancy_match.group(1)
                if link_name == link_target:
                    new_line = f"(= (occupancy {link_name}) {nuova_occupancy})\n"
                    f_out.write(new_line)
                    continue

            # Ogni altra riga (compreso il blocco :goal) resta invariata
            f_out.write(line)

    log.info("Scenario corridor inflow generato correttamente.")
    return output_path


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Esempio concordato: usiamo p05 (goal piu' esigente, intero corridoio)
    path_file = "p05[count=350].pddl"
    file_path = os.path.abspath(
        os.path.join(script_dir, "..", "..", "data", "base_instances", path_file))

    generate_corridor_inflow_scenario(
        file_path=file_path,
        primo_link_corridoio="wrac1_y_wrbc1",
        boost_factor=1.5
    )