Okay, here's the translation of the text into English:

# Videoflix Backend

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-5.1.6-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Backend for Videoflix - a learning project to replicate Netflix with Angular and Django.

This project is the backend for Videoflix, a video streaming web application built as a learning project using Django and Django REST Framework. It serves as a REST API for the frontend (Angular, React, or Vue.js).  Here's the corresponding [Videoflix Frontend](https://github.com/jurin1/videoflix_frontend).

## Table of Contents

1.  Prerequisites
2.  Installation
3.  Environment Variables
4.  Database Migrations
5.  Starting the Development Server
6.  Starting Celery Worker & Beat
7.  Running Tests
8.  Docker (Optional)
9.  API Endpoints (Overview)
10. Contributing
11. License

## 1. Prerequisites

*   Python: Python 3.11 or higher is required. You can download Python from [python.org](https://www.python.org/downloads/).
*   pip: pip is the Python Package Installer, which is usually installed with Python.
*   Virtual Environment (venv recommended): It is highly recommended to use a virtual environment to keep project dependencies isolated.
*   Database:
    *   For development: SQLite (included by default in Django).
    *   For production (recommended): PostgreSQL. Ensure PostgreSQL is installed and configured.
*   Redis: Redis is required for Celery as a broker and potentially for caching. Install and start a Redis server.
*   FFmpeg: FFmpeg is required for video conversion and thumbnail creation. Ensure FFmpeg is installed and available in the system path.
*   Frontend (Optional, for complete app): Angular, React, or Vue.js is recommended for the frontend. However, this repository only contains the backend.

## 2. Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/jurin1/videoflix_backend
    cd videoflix_backend
    ```
    Replace `<repository-url>` with the URL of your GitHub repository.

2.  Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    ```

3.  Activate the virtual environment:
    *   Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4.  Install project dependencies:

    To install all required Python packages, first make sure you have a `requirements.txt` file in the project directory. If it doesn't exist yet, you can create it after installing all the required packages (see note below). Once the `requirements.txt` file exists, run the following command:

    ```bash
    pip install -r requirements.txt
    ```

    **Note about the `requirements.txt` file:**

    The `requirements.txt` file lists all Python packages required for the project. When you first set up the project, or when you add or update new Python packages, you should update the `requirements.txt` file. To create or update the `requirements.txt` file after you have installed all the necessary packages (e.g. with `pip install django restframework ...`), run the following command in the project directory:

    ```bash
    pip freeze > requirements.txt
    ```

    This generated file should then be stored in your repository and committed with the code.

## 3. Environment Variables

Copy the `.env.example` file to `.env` and adjust the variables in the `.env` file to your local environment.

```bash
cp .env.example .env
```

The `.env` file should contain at least the following variables:

```
DATABASE_ENGINE=django.db.backends.postgresql  # or django.db.backends.sqlite3 for SQLite
DATABASE_NAME=videoflix_db
DATABASE_USER=videoflix_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
SECRET_KEY=your_django_secret_key
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend # or other Email Backends
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=your_email@example.com
CELERY_BROKER_URL=redis://localhost:6379/0 # or your Redis Connection URL
FRONTEND_PASSWORD_RESET_URL=http://localhost:4200/password-reset # URL of your Frontend password reset page
```

**Note:** Remember to generate a secure `SECRET_KEY` for production and manage sensitive information such as database passwords and email passwords securely.

## 4. Database Migrations

Run the database migrations to create the database tables:

```bash
python manage.py migrate
```

## 5. Starting the Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The backend API should now be accessible at http://localhost:8000/.

## 6. Starting Celery Worker & Beat

Start the Celery Worker and Celery Beat for processing background tasks (video conversion, periodic tasks):

**Celery Worker** (in a new terminal):

```bash
celery -A videoflix_backend worker -l info
```

**Celery Beat** (in another new terminal):

```bash
celery -A videoflix_backend beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Make sure your Redis server is running before starting Celery.

## 7. Running Tests

To run the backend tests, use `pytest`:

```bash
pytest
```

To measure test coverage and create an HTML report:

```bash
pytest --cov=videos --cov=users --cov-report html
```

The HTML coverage report will be created in the `htmlcov` directory.

## 8. Docker (Optional)

(Here you could add instructions for Docker if you plan to Dockerize. E.g., Dockerfile, `docker-compose.yml`, and instructions for building and starting with Docker Compose)

```bash
# Example Docker Build & Run (needs to be adjusted)
docker-compose up --build
```

## 9. API Endpoints (Overview)

The Videoflix backend provides the following main API endpoints:

*   /api/users/register/: User registration.
*   /api/users/login/: User login and token creation.
*   /api/users/logout/: User logout (token invalidation).
*   /api/users/activate/<uidb64>/<token>/: Account activation via email link.
*   /api/users/password/reset/: Password reset request.
*   /api/users/password/reset/confirm/<uidb64>/<token>/: Password reset confirmation.
*   /api/videos/upload/: Video upload (Admin/Staff users).
* /api/videos/viewing/start/: Start Video Viewing and start/update history.
* /api/videos/viewing/progress/<pk>/: Update video playback progress.
* /api/videos/viewing/finished/<pk>/: Mark video as watched.
* /api/videos/viewing/get/<pk>/: Get the current playback progress.
* /api/videos/viewing/continue-watching/: List of videos the user hasn't finished watching.

For more detailed information about the API endpoints, request bodies, and response formats, see the [API Documentation](LINK_TO_API_DOCUMENTATION - if available). (You could later insert a link here to e.g. an automatically generated API documentation with Swagger or similar)

## 10. Contributing

Contributions are welcome! Please read the `CONTRIBUTING.md` file (if available) for details on the contribution process.

## 11. License

This project is licensed under the MIT License. See the LICENSE file for details.

