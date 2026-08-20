# Generatore Automatico di Istanze Perturbate PDDL+

Questo repository contiene il codice sorgente e i dati per lo sviluppo di un generatore automatico di istanze PDDL+ orientato allo stress-test di sistemi di Urban Traffic Control basati sull'Automated Planning (ENHSP)[cite: 2495].

## Contesto del Progetto e Background Teorico

Il progetto si fonda su due pilastri accademici principali: i paper **ITSC '22** e **ICAPS '24**[cite: 2496].
L'architettura di base sfrutta i dati storici raccolti dai sensori fisici del sistema **SCOOT** nel mondo reale, traducendoli in file PDDL+ per permettere la simulazione e l'ottimizzazione del traffico[cite: 2496].

Il focus centrale del progetto è il rispetto dei **vincoli di deployability** (applicabilità reale)[cite: 2498]:
* I tempi semaforici generati dall'Intelligenza Artificiale non possono essere arbitrari[cite: 2497].
* È obbligatorio utilizzare configurazioni predefinite per gli *stage* (fasi semaforiche)[cite: 2498].
* I tempi di ciclo (*Cycle Time*) devono rimanere costanti per garantire il coordinamento tra gli incroci e il mantenimento della cosiddetta "Onda Verde"[cite: 2498].

Per i test e le simulazioni, il sistema impiegherà il modello PDDL+ identificato come il più efficiente per questi scopi: il **FIRE (Fixed Repetition)**[cite: 2499].

## Obiettivi: La Generazione di Nuove Istanze

L'obiettivo pratico è la creazione di uno script Python capace di leggere istanze storiche "tranquille" (come lo scenario `A_morn`) e modificarle per generare scenari di stress intensivo (Stress-Test)[cite: 2500]. 

Il generatore opera seguendo tre regole ingegneristiche fondamentali:

* **A. Perturbazione Distribuita:** L'algoritmo deve aumentare proporzionalmente i parametri di occupazione stradale (`snapshot_occupancy`) e i flussi attesi (`turnrate`)[cite: 2501]. L'aumento non deve concentrarsi in un singolo incrocio isolato, bensì deve essere distribuito sulla rete per testare la capacità del planner FIRE di bilanciare i "green time" in condizioni di carico globale[cite: 2501].
* **B. Validatore di Realismo (Filtro di Sicurezza):** Le istanze generate sinteticamente non devono mai violare le leggi fisiche del traffico[cite: 2502]. 
    * Il livello di occupazione di un collegamento stradale non può superare il valore di `static_capacity` del link stesso[cite: 2503].
    * La somma matematica delle probabilità di svolta (Turn Rate Probability - TRP) uscenti da un incrocio deve sempre convergere al valore di 1.0 (equivalente al 100% dei veicoli)[cite: 2503].
* **C. Iniezione Topologica (Concert Scenario):** Il generatore include la capacità di simulare onde anomale di traffico[cite: 2504]. Questo avviene bersagliando specificamente i "Boundary Links" (i collegamenti legati al vertice `Outside`), per valutare come l'IA riesca a propagare e smaltire la congestione all'interno del corridoio stradale simulando eventi come l'uscita da uno stadio[cite: 2504].

## Struttura del Repository

Il workspace è organizzato per mantenere una rigorosa separazione tra i dati storici intatti e le istanze generate artificialmente:

* `/src`: Contiene gli script sorgente in Python (parser, generatore logico, validatore di realismo)[cite: 2531].
* `/data/base_instances`: Contiene i file PDDL+ storici originali e non modificati (le baseline)[cite: 2532, 2533].
* `/data/generated_instances`: Directory di destinazione in cui lo script salverà i nuovi file PDDL+ pronti per i test di stress[cite: 2534].
* `/docs`: Cartella dedicata alla documentazione accademica, PDF dei paper e appunti di progetto[cite: 2535].
* `.gitignore`: File di configurazione per escludere file temporanei o cache dal tracciamento[cite: 2530].