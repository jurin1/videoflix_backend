# Videoflix Backend

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-5.1.6-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Backend für Videoflix - ein Lernprojekt zum Nachbau von Netflix mit Angular und Django.

Dieses Projekt ist das Backend für Videoflix, einer Webanwendung zum Streamen von Videos, die als Lernprojekt mit Django und Django REST Framework erstellt wurde. Es dient als REST API für das Frontend (Angular, React oder Vue.js).

## Inhaltsverzeichnis

1. Voraussetzungen
2. Installation
3. Umgebungsvariablen
4. Datenbankmigrationen
5. Entwicklungsserver starten
6. Celery Worker & Beat starten
7. Tests ausführen
8. Docker (Optional)
9. API Endpunkte (Überblick)
10. Beitragen
11. Lizenz
12. Autor

## 1. Voraussetzungen

* Python: Python 3.11 oder höher ist erforderlich. Du kannst Python von [python.org](https://www.python.org/downloads/) herunterladen.
* pip: pip ist der Python Package Installer, der normalerweise mit Python installiert wird.
* Virtual Environment (venv empfohlen): Es wird dringend empfohlen, ein virtuelles Environment zu verwenden, um Projektabhängigkeiten isoliert zu halten.
* Datenbank:
    * Für die Entwicklung: SQLite (standardmäßig in Django enthalten).
    * Für Produktion (empfohlen): PostgreSQL. Stelle sicher, dass PostgreSQL installiert und konfiguriert ist.
* Redis: Redis ist für Celery als Broker und möglicherweise für Caching erforderlich. Installiere und starte einen Redis Server.
* FFmpeg: FFmpeg wird für die Videokonvertierung und Thumbnail-Erstellung benötigt. Stelle sicher, dass FFmpeg installiert und im Systempfad verfügbar ist.
* Frontend (Optional, für vollständige App): Für das Frontend wird Angular, React oder Vue.js empfohlen. Dieses Repository enthält jedoch nur das Backend.

## 2. Installation

1. Repository klonen:
   ```bash
   git clone <repository-url>
   cd videoflix_backend
   ```
   Ersetze `<repository-url>` mit der URL deines GitHub Repositories.

2. Virtuelles Environment erstellen (empfohlen):
   ```bash
   python -m venv venv
   ```

3. Virtuelles Environment aktivieren:
   * Windows:
     ```bash
     venv\Scripts\activate
     ```
   * macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Projektabhängigkeiten installieren:
   Um alle benötigten Python-Pakete zu installieren, stelle zuerst sicher, dass du eine `requirements.txt` Datei im Projektverzeichnis hast. Falls noch nicht vorhanden, kannst du diese erstellen, nachdem du alle benötigten Pakete installiert hast (siehe Hinweis unten). Sobald die `requirements.txt` Datei existiert, führe folgenden Befehl aus:

   ```bash
   pip install -r requirements.txt
   ```

   **Hinweis zur `requirements.txt` Datei:**

   Die `requirements.txt` Datei listet alle Python-Pakete auf, die für das Projekt benötigt werden. Wenn du das Projekt zum ersten Mal einrichtest, oder wenn du neue Python-Pakete hinzufügst oder aktualisierst, solltest du die `requirements.txt` Datei aktualisieren. Um die `requirements.txt` Datei zu erstellen oder zu aktualisieren, nachdem du alle benötigten Pakete installiert hast (z.B. mit `pip install django restframework ...`), führe folgenden Befehl im Projektverzeichnis aus:

   ```bash
   pip freeze > requirements.txt
   ```

   Diese generierte Datei sollte dann in deinem Repository gespeichert und mit dem Code committet werden.

## 3. Umgebungsvariablen

Kopiere die `.env.example` Datei nach `.env` und passe die Variablen in der `.env` Datei an deine lokale Umgebung an.

```bash
cp .env.example .env
```

Die `.env` Datei sollte mindestens folgende Variablen enthalten:

```
DATABASE_ENGINE=django.db.backends.postgresql  # oder django.db.backends.sqlite3 für SQLite
DATABASE_NAME=videoflix_db
DATABASE_USER=videoflix_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
SECRET_KEY=dein_geheimer_django_secret_key
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend # oder andere Email Backends
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=your_email@example.com
CELERY_BROKER_URL=redis://localhost:6379/0 # oder deine Redis Connection URL
FRONTEND_PASSWORD_RESET_URL=http://localhost:4200/password-reset # URL deiner Frontend Passwort Reset Seite
```

**Hinweis:** Vergiss nicht, einen sicheren `SECRET_KEY` für die Produktion zu generieren und sensible Informationen wie Datenbankpasswörter und E-Mail-Passwörter sicher zu verwalten.

## 4. Datenbankmigrationen

Führe die Datenbankmigrationen aus, um die Datenbanktabellen zu erstellen:

```bash
python manage.py migrate
```

## 5. Entwicklungsserver starten

Starte den Django Entwicklungsserver:

```bash
python manage.py runserver
```

Die Backend API sollte nun unter http://localhost:8000/ erreichbar sein.

## 6. Celery Worker & Beat starten

Starte den Celery Worker und Celery Beat für die Verarbeitung von Hintergrundaufgaben (Videokonvertierung, periodische Tasks):

**Celery Worker** (in einem neuen Terminal):

```bash
celery -A videoflix_backend worker -l info
```

**Celery Beat** (in einem weiteren neuen Terminal):

```bash
celery -A videoflix_backend beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Stelle sicher, dass dein Redis Server läuft, bevor du Celery startest.

## 7. Tests ausführen

Um die Backend Tests auszuführen, verwende `pytest`:

```bash
pytest
```

Um die Testabdeckung zu messen und einen HTML Report zu erstellen:

```bash
pytest --cov=videos --cov=users --cov-report html
```

Der HTML Coverage Report wird im `htmlcov` Verzeichnis erstellt.

## 8. Docker (Optional)

(Hier könntest du Anweisungen für Docker hinzufügen, falls du Dockerisierung planst. Z.B. Dockerfile, `docker-compose.yml` und Anweisungen zum Bauen und Starten mit Docker Compose)

```bash
# Beispiel Docker Build & Run (muss noch angepasst werden)
docker-compose up --build
```

## 9. API Endpunkte (Überblick)

Das Videoflix Backend bietet folgende Haupt-API Endpunkte:

* /api/users/register/: Benutzerregistrierung.
* /api/users/login/: Benutzer Login und Token Erstellung.
* /api/users/logout/: Benutzer Logout (Token Inaktivierung).
* /api/users/activate/<uidb64>/<token>/: Account Aktivierung per E-Mail Link.
* /api/users/password/reset/: Passwort Reset Anfrage.
* /api/users/password/reset/confirm/<uidb64>/<token>/: Passwort Reset Bestätigung.
* /api/videos/upload/: Video Upload (Admin/Staff Benutzer).
* /api/videos/viewing/start/: Start Video Viewing und Verlauf starten/aktualisieren.
* /api/videos/viewing/progress/<pk>/: Video Wiedergabefortschritt aktualisieren.
* /api/videos/viewing/finished/<pk>/: Video als fertig angesehen markieren.
* /api/videos/viewing/get/<pk>/: Wiedergabefortschritt abrufen.
* /api/videos/viewing/continue-watching/: Liste der Videos, die der Benutzer noch nicht fertig angesehen hat.

Für detailliertere Informationen zu den API Endpunkten, Request Bodies und Response Formaten, siehe die [API Dokumentation](LINK_ZUR_API_DOKUMENTATION - falls vorhanden). (Du könntest hier später einen Link zu z.B. einer automatisch generierten API Doku mit Swagger oder ähnlichem einfügen)

## 10. Beitragen

Beiträge sind willkommen! Bitte lies die `CONTRIBUTING.md` Datei (falls vorhanden) für Details zum Prozess der Beitragsleistung.

## 11. Lizenz

Dieses Projekt ist unter der MIT Lizenz lizenziert. Siehe die LICENSE Datei für Details.

## 12. Autor

Juri
```