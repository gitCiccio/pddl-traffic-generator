FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Copiamo tutto il necessario nel container (presupponendo che tu abbia la cartella libs del progetto o di ENHSP)
COPY . /app

# Eseguiamo il main specificando il classpath che punta a tutti i file jar presenti nella cartella libs o planner
# (Adattiamo il percorso in base a dove si trovano i tuoi file jar)
ENTRYPOINT ["java", "-jar", "planner/enhsp.jar"]