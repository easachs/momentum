# Momentum

A Django-based habit tracking application.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a .env file with:
   ```
   DJANGO_SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
   ```
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Start the development server:
   ```bash
   honcho start
   ```

## Development

- The main application code is in the `tracker` app
- Templates are stored in `templates/`
- Static files go in `static/`

## Database

Currently using SQLite.