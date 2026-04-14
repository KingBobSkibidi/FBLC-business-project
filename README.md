# FBLC Business Project

A simple Flask + PostgreSQL app for exploring local businesses. Users can register, log in, post a business, save listings, and rate businesses.

## Features

- Explore listings with search, category filters, location filters, and sorting
- Business detail pages with ratings
- Save and unsave businesses
- Post and edit your own business
- Basic account system

## Tech

- Python / Flask
- PostgreSQL via `psycopg`
- HTML + Jinja templates + CSS

## Local setup

1. Create a PostgreSQL database named `locally`.
2. Set environment variables for your local database.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the app:

```bash
python app.py
```

5. Visit `http://127.0.0.1:5000`

The app automatically creates tables on first run using `locally_db.sql`. If you want demo data, leave that file as-is.

## Vercel setup

Vercel can deploy this Flask app directly from `app.py`.

Required environment variables:

- `SECRET_KEY`
- `DATABASE_URL` or Vercel Postgres env vars such as `POSTGRES_URL`

Recommended deployment steps:

1. Import the repo into Vercel.
2. Add a hosted Postgres database.
3. Add `SECRET_KEY` in the Vercel project settings.
4. Deploy.

On first request, the app creates any missing tables automatically. Static assets are served from `public/static` for Vercel compatibility.

## Project structure

- `app.py` Flask backend
- `db.py` database connection and bootstrap logic
- `locally_db.sql` schema and sample data
- `templates/` HTML pages
- `public/static/` CSS for Vercel and local development

## License

MIT
