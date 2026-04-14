# FBLC Business Project (Locally)
A simple Flask + PostgreSQL app for exploring local businesses. Users can register/login, post their business, filter/search, save, and rate businesses.

**Features**
- Explore listings with search, category filter, and sort
- Business detail pages with ratings, and description
- Save/unsave businesses
- Post and edit your own business (1 per user)
- Basic account system

**Tech**
- Python / Flask
- PostgreSQL (psycopg)
- HTML + Jinja templates + CSS

**Setup**
1. Create a PostgreSQL database named `locally`.
2. Install dependencies:
   ```bash
   pip install flask psycopg[binary] werkzeug
   ```
3. Create tables + seed data:
   - Open `locally_db.sql` in pgAdmin → Query Tool → Execute
4. Run the app:
   ```bash
   python app.py
   ```
5. Visit `http://127.0.0.1:5000`

**Seeding Notes**
- `locally_db.sql` includes sample users, businesses, and ratings.

**Project Structure**
- `app.py` Flask backend
- `db.py` DB connection
- `templates/` HTML pages
- `static/` CSS

**License**
MIT
