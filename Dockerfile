# Verwende ein Debian-basiertes Python-Image mit Bash
FROM python:3.11

# Setze das Arbeitsverzeichnis
WORKDIR /app

# Installiere Systemabhängigkeiten (inkl. Bash & PostgreSQL-Dev)
RUN apt-get update && apt-get install -y \
    bash \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Kopiere die Anforderungen und installiere sie
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den gesamten Code ins Image
COPY . .

# Stelle sicher, dass der Medienordner existiert (falls leer)
RUN mkdir -p /app/media

# Setze die richtigen Berechtigungen (optional)
RUN chmod -R 755 /app/media

# Django läuft auf Port 8000
EXPOSE 8000  

# Starte die Anwendung mit Bash und Django
CMD ["bash", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
