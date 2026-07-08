# Locally: Flask app for exploring, posting, saving, and rating local businesses.
import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db_connection

app = Flask(__name__)
# random fallback keeps dev sessions unforgeable; set SECRET_KEY in production
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

BUSINESS_CATEGORIES = [
    "Restaurant",
    "Clothing",
    "Technology",
    "Health",
    "Automotive",
    "Home Service (Repair)",
    "Other",
]

# whitelist of ORDER BY clauses; user input never reaches the SQL string
SORT_ORDERS = {
    "rating": "avg_rating DESC NULLS LAST, rating_count DESC, b.id DESC",
    "rating_low": "avg_rating ASC NULLS FIRST, rating_count DESC, b.id DESC",
    "oldest": "b.id ASC",
}


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def safe_referrer():
    # only redirect back to our own pages, never an external URL
    ref = request.referrer
    return ref if ref and ref.startswith(request.host_url) else url_for("index")


def business_form_fields():
    """Validate the post/edit business form. Returns (fields, error_response)."""
    fields = {k: request.form.get(k, "").strip()
              for k in ("name", "category", "description", "location")}
    if not all(fields.values()):
        return None, ("All fields are required.", 400)
    if fields["category"] not in BUSINESS_CATEGORIES:
        return None, ("Invalid category selected.", 400)
    return fields, None


@app.route("/")
def index():
    category = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    sort_by = request.args.get("sort", "").strip()

    conditions, params = [], []
    if category:
        conditions.append("b.category = %s")
        params.append(category)
    if search:
        conditions.append("b.name ILIKE %s")
        params.append(f"%{search}%")
    if location:
        conditions.append("b.location ILIKE %s")
        params.append(f"%{location}%")

    query = """
        SELECT b.id, b.name, b.category, b.description, b.location,
               AVG(r.rating) AS avg_rating, COUNT(r.rating) AS rating_count
        FROM businesses b
        LEFT JOIN ratings r ON r.business_id = b.id
    """
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " GROUP BY b.id ORDER BY " + SORT_ORDERS.get(sort_by, "b.id DESC")

    saved_ids = []
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(query, params)
        businesses = cur.fetchall()
        if "user_id" in session:
            cur.execute("SELECT business_id FROM saved_businesses WHERE user_id = %s",
                        (session["user_id"],))
            saved_ids = [row["business_id"] for row in cur.fetchall()]

    return render_template(
        "index.html",
        businesses=businesses,
        saved_business_ids=saved_ids,
        categories=BUSINESS_CATEGORIES,
        selected_category=category,
        search_term=search,
        location_filter=location,
        selected_sort=sort_by,
    )


@app.route("/business/<int:business_id>")
def business_details(business_id):
    user_id = session.get("user_id")
    user_rating, is_saved = None, False

    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, category, description, location FROM businesses WHERE id = %s",
                    (business_id,))
        business = cur.fetchone()
        if not business:
            return "Business not found.", 404

        cur.execute("SELECT AVG(rating) AS avg_rating, COUNT(*) AS rating_count FROM ratings WHERE business_id = %s",
                    (business_id,))
        stats = cur.fetchone()

        if user_id:
            cur.execute("SELECT rating FROM ratings WHERE user_id = %s AND business_id = %s",
                        (user_id, business_id))
            row = cur.fetchone()
            user_rating = row["rating"] if row else None
            cur.execute("SELECT 1 FROM saved_businesses WHERE user_id = %s AND business_id = %s",
                        (user_id, business_id))
            is_saved = cur.fetchone() is not None

    return render_template(
        "business_details.html",
        business=business,
        avg_rating=stats["avg_rating"],
        rating_count=stats["rating_count"],
        user_rating=user_rating,
        is_saved=is_saved,
    )


@app.route("/rate-business/<int:business_id>", methods=["POST"])
@login_required
def rate_business(business_id):
    rating = request.form.get("rating", "")
    if rating not in {"1", "2", "3", "4", "5"}:
        return "Invalid rating.", 400

    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM businesses WHERE id = %s", (business_id,))
        if not cur.fetchone():
            return "Business not found.", 404
        cur.execute(
            """
            INSERT INTO ratings (user_id, business_id, rating) VALUES (%s, %s, %s)
            ON CONFLICT (user_id, business_id) DO UPDATE SET rating = EXCLUDED.rating
            """,
            (session["user_id"], business_id, int(rating)),
        )
    return redirect(url_for("business_details", business_id=business_id))


@app.route("/save-business/<int:business_id>", methods=["POST"])
@login_required
def save_business(business_id):
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO saved_businesses (user_id, business_id)
            SELECT %s, id FROM businesses WHERE id = %s
            ON CONFLICT (user_id, business_id) DO NOTHING
            """,
            (session["user_id"], business_id),
        )
    return redirect(safe_referrer())


@app.route("/unsave-business/<int:business_id>", methods=["POST"])
@login_required
def unsave_business(business_id):
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM saved_businesses WHERE user_id = %s AND business_id = %s",
                    (session["user_id"], business_id))
    return redirect(safe_referrer())


@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.execute("SELECT * FROM businesses WHERE owner_id = %s", (user_id,))
        user_business = cur.fetchone()
        cur.execute(
            """
            SELECT b.id, b.name, b.category, b.description, b.location,
                   AVG(r.rating) AS avg_rating, COUNT(r.rating) AS rating_count
            FROM saved_businesses s
            JOIN businesses b ON b.id = s.business_id
            LEFT JOIN ratings r ON r.business_id = b.id
            WHERE s.user_id = %s
            GROUP BY s.id, b.id
            ORDER BY s.id DESC
            """,
            (user_id,),
        )
        saved_businesses = cur.fetchall()

    return render_template("profile.html", user=user, user_business=user_business,
                           saved_businesses=saved_businesses)


@app.route("/post-business", methods=["GET", "POST"])
@login_required
def post_business():
    user_id = session["user_id"]
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM businesses WHERE owner_id = %s", (user_id,))
        if cur.fetchone():
            return "You have already posted a business. Only one allowed per user."

        if request.method == "POST":
            fields, error = business_form_fields()
            if error:
                return error
            cur.execute(
                "INSERT INTO businesses (owner_id, name, category, description, location) VALUES (%s, %s, %s, %s, %s)",
                (user_id, fields["name"], fields["category"], fields["description"], fields["location"]),
            )
            return redirect(url_for("profile"))

    return render_template("business_form.html", business=None, categories=BUSINESS_CATEGORIES)


@app.route("/edit-business", methods=["GET", "POST"])
@login_required
def edit_business():
    user_id = session["user_id"]
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM businesses WHERE owner_id = %s", (user_id,))
        business = cur.fetchone()
        if not business:
            return redirect(url_for("post_business"))

        if request.method == "POST":
            fields, error = business_form_fields()
            if error:
                return error
            cur.execute(
                "UPDATE businesses SET name = %s, category = %s, description = %s, location = %s WHERE owner_id = %s",
                (fields["name"], fields["category"], fields["description"], fields["location"], user_id),
            )
            return redirect(url_for("profile"))

    return render_template("business_form.html", business=business, categories=BUSINESS_CATEGORIES)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, username, password_hash FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()  # prevent session fixation
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        return "Invalid email or password.", 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        if not (username and email and password):
            return "All fields are required.", 400

        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE email = %s OR username = %s", (email, username))
            if cur.fetchone():
                return "Registration failed. Email or username already in use.", 409
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, generate_password_hash(password)),
            )
        return redirect(url_for("login"))

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
