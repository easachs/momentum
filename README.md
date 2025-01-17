# Momentum

A Django-based tracking application.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use: env\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a .env file with:
   ```
   DJANGO_SECRET_KEY=your-secret-key-here
   ```
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Development

- The main application code is in the `tracker` app
- Templates are stored in `templates/`
- Static files go in `static/`

## Database

Currently using SQLite for development. To switch to PostgreSQL:

1. Create a PostgreSQL database
2. Update database settings in settings.py
3. Run migrations