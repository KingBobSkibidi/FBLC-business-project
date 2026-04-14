# main flask app for Locally (routes, db queries and login sessions)

#import statements
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

# create flask app instance
app = Flask(__name__)

# session signing key (used to protect cookies)
app.secret_key = "dev-secret-key"

# list of business categories
BUSINESS_CATEGORIES = [
    "Restaurant",
    "Clothing",
    "Technology",
    "Health",
    "Automotive",
    "Home Service (Repair)",
    "Other",
]

#explore/index page
@app.route("/")
def index():

    # connect to database
    conn = get_db_connection()
    cur = conn.cursor()

    # fetch filter values from url query parameters
    category_filter = request.args.get("category", "").strip()
    search_term = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "").strip()
    location_filter = request.args.get("location", "").strip()

    #fetch businesses info (with ratings)
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

    # add category filter condition
    if category_filter:
        conditions.append("b.category = %s")
        params.append(category_filter)

    # add search filter condition (case-insensitive)
    if search_term:
        conditions.append("b.name ILIKE %s")
        pattern = f"%{search_term}%"
        params.append(pattern)

    # add location filter condition (case-insensitive)
    if location_filter:
        conditions.append("b.location ILIKE %s")
        pattern = f"%{location_filter}%"
        params.append(pattern)

    # apply WHERE clause if any conditions exist
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # choose sort order
    order_clause = "b.id DESC"
    if sort_by == "rating":
        order_clause = "avg_rating DESC NULLS LAST, rating_count DESC, b.id DESC"
    elif sort_by == "rating_low":
        order_clause = "avg_rating ASC NULLS FIRST, rating_count DESC, b.id DESC"
    elif sort_by == "oldest":
        order_clause = "b.id ASC"

    # finish query with GROUP BY + ORDER BY
    query += f"""
        GROUP BY b.id, b.name, b.category, b.description, b.location
        ORDER BY {order_clause}
    """
    cur.execute(query, params)
    businesses = cur.fetchall()

    # fetch saved business ids for user (for save button)
    saved_business_ids = []
    if "user_id" in session:
        cur.execute("SELECT business_id FROM saved_businesses WHERE user_id = %s", (session["user_id"],))
        saved_business_ids = [row["business_id"] for row in cur.fetchall()]
    
    # close database
    cur.close()
    conn.close()

    # render explore page template
    return render_template(
        "index.html",
        businesses=businesses,
        saved_business_ids=saved_business_ids,
        categories=BUSINESS_CATEGORIES,
        selected_category=category_filter,
        search_term=search_term,
        location_filter=location_filter,
        selected_sort=sort_by,
    )

# business details page
@app.route("/business/<int:business_id>")
def business_details(business_id):

    # connect to database
    conn = get_db_connection()
    cur = conn.cursor()
    
    # fetch business info by id
    cur.execute(
        "SELECT id, name, category, description, location FROM businesses WHERE id = %s",
        (business_id,),
    )
    business = cur.fetchone()

    # return 404 if business does not exist
    if not business:
        cur.close()
        conn.close()
        return "Business not found.", 404

    # fetch ratings for the business
    cur.execute(
        """
        SELECT AVG(rating) AS avg_rating, COUNT(*) AS rating_count
        FROM ratings
        WHERE business_id = %s
        """,
        (business_id,),
    )
    rating_stats = cur.fetchone()

    # fetch user's rating (if any) 
    user_rating = None
    is_saved = False
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
    
        # fetch user's saved status
        cur.execute(
            """
            SELECT 1
            FROM saved_businesses
            WHERE user_id = %s AND business_id = %s
            """,
            (session["user_id"], business_id),
        )
        is_saved = cur.fetchone() is not None

    # close database
    cur.close()
    conn.close()

    # render business details page template
    return render_template(
        "business_details.html",
        business=business,
        avg_rating=rating_stats["avg_rating"],
        rating_count=rating_stats["rating_count"],
        user_rating=user_rating,
        is_saved=is_saved,
    )

# handle rating submission
@app.route("/rate-business/<int:business_id>", methods=["POST"])
def rate_business(business_id):

    # require login
    if "user_id" not in session:
        return redirect(url_for("login"))

    # fetch rating from form
    rating_value = request.form.get("rating", "").strip()
    try:
        rating_value = int(rating_value)
    except ValueError:
        return "Invalid rating.", 400

    # validate rating (range 1-5)
    if rating_value < 1 or rating_value > 5:
        return "Invalid rating.", 400

    # connect to database
    conn = get_db_connection()
    cur = conn.cursor()

    # confirm business exists
    cur.execute("SELECT id FROM businesses WHERE id = %s", (business_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return "Business not found.", 404

    # insert or update rating
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

    # close database
    cur.close()
    conn.close()

    # redirect back to business details
    return redirect(url_for("business_details", business_id=business_id))

# save business action (button)
@app.route("/save-business/<int:business_id>", methods=["POST"])
def save_business(business_id):

    # require login
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # connect to database
    conn = get_db_connection()
    cur = conn.cursor()

    # save business if it exists, ignore if already saved
    cur.execute(
        """
        INSERT INTO saved_businesses (user_id, business_id)
        SELECT %s, id FROM businesses WHERE id = %s
        ON CONFLICT (user_id, business_id) DO NOTHING
        """,
        (user_id, business_id),
    )
    conn.commit()

    # close database
    cur.close()
    conn.close()

    # redirect back to previous/index page
    return redirect(request.referrer or url_for("index"))

# unsave business action (button)
@app.route("/unsave-business/<int:business_id>", methods=["POST"])
def unsave_business(business_id):

    # require login
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # connect to database
    conn = get_db_connection()
    cur = conn.cursor()

    # delete saved business under user
    cur.execute(
        "DELETE FROM saved_businesses WHERE user_id = %s AND business_id = %s",
        (user_id, business_id),
    )
    conn.commit()

    # close database
    cur.close()
    conn.close()

    # redirect back to previous/index page
    return redirect(request.referrer or url_for("index"))

#profile page
@app.route("/profile")
def profile():

    # require login
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    
    # connect to database
    conn = get_db_connection()
    cur = conn.cursor()

    # fetch user account info
    cur.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone() 

    # fetch user's posted business
    cur.execute("SELECT * FROM businesses WHERE owner_id = %s", (user_id,))
    user_business = cur.fetchone()

    # fetch user's saved businesses and rating 
    cur.execute(
        """
        SELECT
            b.id,
            b.name,
            b.category,
            b.description,
            b.location,
            AVG(r.rating) AS avg_rating,
            COUNT(r.rating) AS rating_count
        FROM saved_businesses
        JOIN businesses b ON b.id = saved_businesses.business_id
        LEFT JOIN ratings r ON r.business_id = b.id
        WHERE saved_businesses.user_id = %s
        GROUP BY saved_businesses.id, b.id, b.name, b.category, b.description, b.location
        ORDER BY saved_businesses.id DESC
        """,
        (user_id,)
    )
    saved_businesses = cur.fetchall()

    # close database
    cur.close()
    conn.close()

    # render profile page template
    return render_template("profile.html", user=user, user_business=user_business, saved_businesses=saved_businesses)

#post business page
@app.route("/post-business", methods=["GET", "POST"])
def post_business():

    # require login
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # connect to database
    conn = get_db_connection()
    cur = conn.cursor()

    # prevent multiple businesses per user
    cur.execute("SELECT * FROM businesses WHERE owner_id = %s", (user_id,))
    existing = cur.fetchone()

    if existing: #if they already have a business
        cur.close()
        conn.close()
        return "You have already posted a business. Only one allowed per user."

    # handle business post form submission
    if request.method == "POST":
        name = request.form["name"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        location = request.form["location"].strip()

        # validate category
        if category not in BUSINESS_CATEGORIES:
            cur.close()
            conn.close()
            return "Invalid category selected."

        # insert business
        cur.execute(
            "INSERT INTO businesses (owner_id, name, category, description, location) VALUES (%s, %s, %s, %s, %s)", #%s placeholder, avoid sql injection
            (user_id, name, category, description, location),
        )
        conn.commit()

        # close database
        cur.close()
        conn.close()

        # redirect to profile page after posting
        return redirect(url_for("profile")) 

    # if GET request, close database and render business post form
    cur.close()
    conn.close()
    return render_template("post_business.html", categories=BUSINESS_CATEGORIES)

# edit business page
@app.route("/edit-business", methods=["GET", "POST"])
def edit_business():

    # require login
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # connect to database
    conn = get_db_connection()
    cur = conn.cursor()

    # fetch user's business
    cur.execute("SELECT * FROM businesses WHERE owner_id = %s", (user_id,))
    business = cur.fetchone()

    # redirect to post business page if no business exists
    if not business:
        cur.close()
        conn.close()
        return redirect(url_for("post_business"))

    # handle business post/edit form submission
    if request.method == "POST":
        name = request.form["name"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        location = request.form["location"].strip()

        # validate category
        if category not in BUSINESS_CATEGORIES:
            cur.close()
            conn.close()
            return "Invalid category selected."

        # update business info
        cur.execute(
            """
            UPDATE businesses
            SET name = %s, category = %s, description = %s, location = %s
            WHERE owner_id = %s
            """,
            (name, category, description, location, user_id),
        )
        conn.commit()

        # close database
        cur.close()
        conn.close()

        # redirect to profile after update
        return redirect(url_for("profile"))

    # if GET request, close database and render business edit form
    cur.close()
    conn.close()
    return render_template("edit_business.html", business=business, categories=BUSINESS_CATEGORIES,)

#login page
@app.route("/login", methods=["GET", "POST"])
def login():

    # handle login submission
    if request.method=="POST": 
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        # connect to database
        conn = get_db_connection()
        cur = conn.cursor()

        # fetch user by email
        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE email = %s", #%s placeholder, avoid sql injection
            (email,)
        )
        user = cur.fetchone() #fetch single row returned by the query; safe because emails are unique”

        # close database
        cur.close()
        conn.close()

        # if correct login, store user data for session and redirect to explore page
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))

        return "Invalid email or password" #incorrect login
    
    # render login page
    return render_template("login.html")

#logout action
@app.route("/logout")
def logout():
    # clear all session keys
    session.clear()
    return redirect(url_for("index"))

#register page
@app.route("/register", methods=["GET", "POST"])
def register():

    # handle registration submission
    if request.method == "POST": 
        username = request.form["username"].strip() 
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        
        # hash password before saving
        password_hash = generate_password_hash(password)
        
        # connect to database
        conn = get_db_connection()
        cur = conn.cursor()

        # check for existing email or username
        cur.execute(
            "SELECT id FROM users WHERE email = %s OR username = %s",
            (email, username),
        )
        existing_user = cur.fetchone()

        # if account with login info exists
        if existing_user:
            cur.close()
            conn.close()
            return "Registration failed. Email or username already in use."

        # insert new user
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        conn.commit()

        # close database
        cur.close()
        conn.close()

        # redirect to login page after registering
        return redirect(url_for("login")) 

    #render register page
    return render_template("register.html") 

# run local dev server
if __name__ == "__main__":
    app.run(debug=True)
