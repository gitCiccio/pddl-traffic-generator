"""Convert an ENHSP console log into a PPS plan (UTF-8, no BOM)."""

from __future__ import annotations

import argparse
import re
import sys
from decimal import Decimal
from pathlib import Path


ACTION = re.compile(r"^\s*(\d+(?:\.\d+)?):\s*(\([^\r\n]*\))\s*$")
WAITING = re.compile(r"^\s*\d+(?:\.\d+)?:\s*-+waiting-+\s*\[[^\]]+\]\s*$", re.I)
ELAPSED = re.compile(r"^\s*Elapsed Time:\s*(\d+(?:\.\d+)?)\s*$", re.I)
PLAN_END = re.compile(r"^\s*\d+(?:\.\d+)?:\s*@PlanEND\s*$", re.I)


def read_log(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def convert(log: str, expected_end: Decimal | None) -> tuple[str, int, Decimal]:
    lines = log.splitlines()
    solved = [i for i, line in enumerate(lines) if line.strip() == "Problem Solved"]
    starts = [i for i, line in enumerate(lines) if line.strip() == "Found Plan:"]
    if len(solved) != 1 or len(starts) != 1 or solved[0] >= starts[0]:
        raise ValueError("Serve un output ENHSP completo con un solo 'Problem Solved' e 'Found Plan:'.")

    elapsed_values = [Decimal(match.group(1)) for line in lines
                      if (match := ELAPSED.match(line))]
    if len(elapsed_values) != 1:
        raise ValueError("'Elapsed Time' assente o presente più volte nell'output.")
    end = elapsed_values[0]
    if expected_end is not None and end != expected_end:
        raise ValueError(f"Piano terminato a {end} s; erano attesi {expected_end} s.")

    actions: list[str] = []
    last_time = Decimal("0")
    for line in lines[starts[0] + 1:]:
        if line.startswith("Plan-Length:"):
            break
        if not line.strip() or WAITING.match(line):
            continue
        if PLAN_END.match(line):
            raise ValueError("L'output contiene già @PlanEND nella sezione del piano.")
        match = ACTION.match(line)
        if not match:
            raise ValueError(f"Riga inattesa nella sezione del piano: {line!r}")
        instant = Decimal(match.group(1))
        if instant < last_time or instant > end:
            raise ValueError(f"Azione fuori ordine o oltre la fine del piano: {line!r}")
        last_time = instant
        actions.append(f"{match.group(1)}: {match.group(2)}")
    else:
        raise ValueError("Sezione del piano incompleta: manca 'Plan-Length:'.")

    output = "\n".join((*actions, f"{end}: @PlanEND")) + "\n"
    return output, len(actions), end


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Output completo di ENHSP (.txt)")
    parser.add_argument("output", type=Path, help="Piano per PPS (.plan)")
    parser.add_argument("--expected-end", type=Decimal, metavar="SECONDS",
                        help="Rifiuta il piano se Elapsed Time differisce da questo valore")
    args = parser.parse_args()

    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Input e output devono essere file diversi.")
        plan, count, end = convert(read_log(args.input), args.expected_end)
        args.output.write_text(plan, encoding="utf-8", newline="\n")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Errore: {error}", file=sys.stderr)
        return 1

    print(f"Creato {args.output}: {count} azioni, @PlanEND a {end} s (UTF-8).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
