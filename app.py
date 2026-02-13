from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "dev-secret-key"

BUSINESS_CATEGORIES = [
    "Restaurant",
    "Clothing",
    "Tech",
    "Automotive",
    "Health",
    "Home Service (Repair)",
    "Other",
]

#explore page/function
@app.route("/")
def index():
    #initialize
    conn = get_db_connection()
    cur = conn.cursor()

    category_filter = request.args.get("category", "").strip()
    search_term = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "").strip()

    #get businesses info (with ratings)
    query = """
        SELECT
            b.id,
            b.name,
            b.category,
            b.description,
            b.location,
            AVG(r.rating) AS avg_rating,
            COUNT(r.rating) AS rating_count
        FROM businesses b
        LEFT JOIN ratings r ON r.business_id = b.id
    """
    params = []
    conditions = []

    if category_filter:
        conditions.append("b.category = %s")
        params.append(category_filter)

    if search_term:
        conditions.append("b.name ILIKE %s")
        pattern = f"%{search_term}%"
        params.append(pattern)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    order_clause = "b.id DESC"
    if sort_by == "rating":
        order_clause = "avg_rating DESC NULLS LAST, rating_count DESC, b.id DESC"
    elif sort_by == "rating_low":
        order_clause = "avg_rating ASC NULLS FIRST, rating_count DESC, b.id DESC"
    elif sort_by == "oldest":
        order_clause = "b.id ASC"

    query += f"""
        GROUP BY b.id, b.name, b.category, b.description, b.location
        ORDER BY {order_clause}
    """
    cur.execute(query, params)
    businesses = cur.fetchall()

    saved_business_ids = []
    if "user_id" in session:
        cur.execute("SELECT business_id FROM saved_businesses WHERE user_id = %s", (session["user_id"],))
        saved_business_ids = [row["business_id"] for row in cur.fetchall()]
    
    #close cursor and database
    cur.close()
    conn.close()

    return render_template(
        "index.html",
        businesses=businesses,
        saved_business_ids=saved_business_ids,
        categories=BUSINESS_CATEGORIES,
        selected_category=category_filter,
        search_term=search_term,
        selected_sort=sort_by,
    )

@app.route("/business/<int:business_id>")
def business_details(business_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, category, description, location FROM businesses WHERE id = %s",
        (business_id,),
    )
    business = cur.fetchone()

    if not business:
        cur.close()
        conn.close()
        return "Business not found.", 404

    cur.execute(
        """
        SELECT AVG(rating) AS avg_rating, COUNT(*) AS rating_count
        FROM ratings
        WHERE business_id = %s
        """,
        (business_id,),
    )
    rating_stats = cur.fetchone()

    user_rating = None
    if "user_id" in session:
        cur.execute(
            """
            SELECT rating
            FROM ratings
            WHERE user_id = %s AND business_id = %s
            """,
            (session["user_id"], business_id),
        )
        user_row = cur.fetchone()
        if user_row:
            user_rating = user_row["rating"]

    cur.close()
    conn.close()

    return render_template(
        "business_details.html",
        business=business,
        avg_rating=rating_stats["avg_rating"],
        rating_count=rating_stats["rating_count"],
        user_rating=user_rating,
    )

@app.route("/rate-business/<int:business_id>", methods=["POST"])
def rate_business(business_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    rating_value = request.form.get("rating", "").strip()
    try:
        rating_value = int(rating_value)
    except ValueError:
        return "Invalid rating.", 400

    if rating_value < 1 or rating_value > 5:
        return "Invalid rating.", 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM businesses WHERE id = %s", (business_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return "Business not found.", 404

    cur.execute(
        """
        INSERT INTO ratings (user_id, business_id, rating)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, business_id)
        DO UPDATE SET rating = EXCLUDED.rating
        """,
        (session["user_id"], business_id, rating_value),
    )
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("business_details", business_id=business_id))

@app.route("/save-business/<int:business_id>", methods=["POST"])
def save_business(business_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO saved_businesses (user_id, business_id)
        SELECT %s, id FROM businesses WHERE id = %s
        ON CONFLICT (user_id, business_id) DO NOTHING
        """,
        (user_id, business_id),
    )

    conn.commit()

    #close cursor and database
    cur.close()
    conn.close()

    return redirect(request.referrer or url_for("index"))

@app.route("/unsave-business/<int:business_id>", methods=["POST"])
def unsave_business(business_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM saved_businesses WHERE user_id = %s AND business_id = %s",
        (user_id, business_id),
    )
    conn.commit()

    cur.close()
    conn.close()

    return redirect(request.referrer or url_for("index"))

#profile page/function
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    
    conn = get_db_connection()
    cur = conn.cursor()

    #get user's info
    cur.execute("SELECT username, email FROM users WHERE id = %s", (user_id,)) #%s placeholder, avoid sql injection
    user = cur.fetchone() 

    cur.execute("SELECT * FROM businesses WHERE owner_id = %s", (user_id,))
    user_business = cur.fetchone()

    #get user's saved businesses
    cur.execute(
        """
        SELECT b.id, b.name, b.category, b.description, b.location
        FROM saved_businesses sb
        JOIN businesses b ON b.id = sb.business_id
        WHERE sb.user_id = %s
        ORDER BY sb.id DESC
        """,
        (user_id,)
    )
    saved_businesses = cur.fetchall()

    #close cursor and database
    cur.close()
    conn.close()

    return render_template("profile.html", user=user, user_business=user_business, saved_businesses=saved_businesses)

#post business page/function
@app.route("/post-business", methods=["GET", "POST"])
def post_business():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM businesses WHERE owner_id = %s", (user_id,))
    existing = cur.fetchone()

    if existing: #if they already have a business
        cur.close()
        conn.close()
        return "You have already posted a business. Only one allowed per user."

    if request.method == "POST":
        name = request.form["name"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        location = request.form["location"].strip()

        if category not in BUSINESS_CATEGORIES:
            cur.close()
            conn.close()
            return "Invalid category selected."

        cur.execute(
            "INSERT INTO businesses (owner_id, name, category, description, location) VALUES (%s, %s, %s, %s, %s)", #%s placeholder, avoid sql injection
            (user_id, name, category, description, location),
        )
        conn.commit()

        #close cursor and database
        cur.close()
        conn.close()

        return redirect(url_for("profile")) #after posting, go back to profile

    #if GET request, just show the form
    cur.close()
    conn.close()
    return render_template("post_business.html", categories=BUSINESS_CATEGORIES)

@app.route("/edit-business", methods=["GET", "POST"])
def edit_business():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM businesses WHERE owner_id = %s", (user_id,))
    business = cur.fetchone()

    if not business:
        cur.close()
        conn.close()
        return redirect(url_for("post_business"))

    if request.method == "POST":
        name = request.form["name"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        location = request.form["location"].strip()

        if category not in BUSINESS_CATEGORIES:
            cur.close()
            conn.close()
            return "Invalid category selected."

        cur.execute(
            """
            UPDATE businesses
            SET name = %s, category = %s, description = %s, location = %s
            WHERE owner_id = %s
            """,
            (name, category, description, location, user_id),
        )
        conn.commit()

        cur.close()
        conn.close()
        return redirect(url_for("profile"))

    cur.close()
    conn.close()
    return render_template(
        "edit_business.html",
        business=business,
        categories=BUSINESS_CATEGORIES,
    )

#login page/function
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method=="POST": 
        #get user input and initialize
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        conn = get_db_connection()
        cur = conn.cursor()

        #query
        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE email = %s", #%s placeholder, avoid sql injection
            (email,)
        )
        user = cur.fetchone() #fetch single row returned by the query; safe because emails are unique”

        #close cursor and database
        cur.close()
        conn.close()

        #if correct login, store user data for session and redirect to profile
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))

        return "Invalid email or password" #incorrect login
    
    return render_template("login.html") #display login page when called

#logout function
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#register page/function
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST": 
        #get user input and initialize
        username = request.form["username"].strip() 
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM users WHERE email = %s OR username = %s",
            (email, username),
        )
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            conn.close()
            return "Registration failed. Email or username already in use."

        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", #%s placeholder, avoid sql injection
            (username, email, password_hash)
        )
        conn.commit()

        cur.close()
        conn.close()

        return redirect(url_for("login")) #redirect to login 

    return render_template("register.html") #display register page when called

#test
if __name__ == "__main__":
    app.run(debug=True)
