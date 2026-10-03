# Esperimenti e risultati

I domini sono in `domains/`, i problemi in `data/` e gli output ENHSP/PPS in questa cartella. Ogni sottocartella rappresenta uno scenario; non rinominare i file di input quando si ripete un esperimento senza aggiornare questa mappa.

| Scenario | Dominio | Problema | Risultati | Confrontabile a 900 s? |
|---|---|---|---|---|
| Baseline 15 min | `domains/domain_baseline_15min.pddl` | `data/generated_instances/p05_baseline_15min.pddl` | `results/baseline_15min/` | Sì |
| Profilo variabile 15 min | `domains/domain_traffic_profile_15min.pddl` | `data/generated_instances/p05_traffic_profile_15min.pddl` | `results/profile_15min/` | Sì |
| Baseline esplorativo | `domains/domain.pddl` | `data/base_instances/p05[count=350].pddl` | `results/legacy_baseline/` | No: goal da 350 e durata 1663 s |
| Stress esplorativo +50% | `domains/domain.pddl` | `data/generated_instances/p05_increased_stress_level.pddl` | `results/legacy_stress_50pct/` | No: goal da 350 e durata 1659 s |

Ogni cartella con log completo usa gli stessi nomi: `enhsp_output.txt`, `plan.plan` (UTF-8) e `pps_trace.txt`. La cartella `profile_15min` conserva anche `plan_raw_utf16.plan`, la prima copia manuale: **per PPS usare soltanto `plan.plan`**. Il log ENHSP completo di questo scenario non è disponibile; non è stato ricreato o inventato. Le cartelle `legacy_*` conservano i risultati precedenti senza modificarne i contenuti.

Provenienza dei file spostati dalla radice:

| Cartella | Vecchi nomi |
|---|---|
| `baseline_15min` | `baseline_15min_output_V2.txt`, `baseline_15min.plan`, `baseline_15min_trace.txt` |
| `profile_15min` | `traffic_profile_15min_output.plan`, `traffic_profile_15min.plan`, `traffic_profile_15min_trace.txt` |
| `legacy_baseline` | `baseline_output.txt`, `baseline.plan`, `baseline_trace.txt` |
| `legacy_stress_50pct` | `increased_stress_output.txt`, `stressedline.plan`, `stressedline_trace.txt` |

Il confronto finale richiede ancora uno scenario `constant_peak_15min`: usare `domain_baseline_15min.pddl` e una copia del problema baseline con il solo turnrate d'ingresso iniziale a `0.7110`.

Per nuovi esperimenti, salvare l'output ENHSP nella rispettiva sottocartella e convertirlo con `scripts/enhsp_to_pps_plan.py`; lo script verifica `Problem Solved`, `Elapsed Time` e produce UTF-8 senza BOM. Con `--expected-end 900` rifiuta piani che non terminano esattamente a 900 s.
