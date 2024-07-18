# Verwende ein offizielles Python-Image als Basis
FROM python:3.9-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die Anforderungen-Datei in das Arbeitsverzeichnis
COPY requirements.txt requirements.txt

# Installiere die Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest des Anwendungscodes in das Arbeitsverzeichnis
COPY . .

# Setze Umgebungsvariablen für Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Exponiere den Port, auf dem Flask läuft
EXPOSE 5000

# Führe die Anwendung aus
CMD ["flask", "run"]
