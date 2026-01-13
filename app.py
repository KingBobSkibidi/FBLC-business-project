from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
from functools import wraps

app = Flask(__name__)
app.secret_key = "dev-secret-key"

#login_required decorator
def login_required(f): #f is placeholder for original function
    @wraps(f) #@wraps copies original meta data
    def decorated_function(): #wrapper

        #check if user not logged in
        if "user_id" not in session:
            return redirect(url_for("login"))
        
        return f() #call original function if logged in
    
    return decorated_function #return the wrapped function to replace original

#Explore page/function
@app.route("/")
def index():
    return render_template("index.html")

#profile page/function
@app.route("/profile")
@login_required
def profile():
    #initialize
    user_id = session["user_id"]
    
    conn = get_db_connection()
    cur = conn.cursor()

    #get user's info
    cur.execute("SELECT username, email FROM users WHERE id = %s", (user_id,)) #%s placeholder, avoid sql injection
    user = cur.fetchone() 

    #get user's business if it exists
    cur.execute("SELECT * FROM businesses WHERE owner_id = %s", (user_id,)) #%s placeholder, avoid sql injection
    user_business = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("profile.html", user=user, user_business=user_business)

#post business page/function
@app.route("/post-business", methods=["GET", "POST"])
@login_required
def post_business():
    #initialize
    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    #check if user already has a business
    cur.execute("SELECT * FROM businesses WHERE owner_id = %s", (user_id,)) #%s placeholder, avoid sql injection
    existing = cur.fetchone()

    if existing: #if they already have a business
        cur.close()
        conn.close()
        return "You have already posted a business. Only one allowed per user."

    if request.method == "POST":
        #get form data
        name = request.form["name"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        location = request.form["location"].strip()

        try:
            # Insert into database
            cur.execute(
                "INSERT INTO businesses (owner_id, name, category, description, location) VALUES (%s, %s, %s, %s, %s)", #%s placeholder, avoid sql injection
                (user_id, name, category, description, location) 
            )
            conn.commit()

        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            return "Failed to post business. Please try again later."

        #close cursor and database
        cur.close()
        conn.close()

        return redirect(url_for("profile")) #after posting, go back to profile

    #if GET request, just show the form
    cur.close()
    conn.close()
    return render_template("post_business.html")

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

        #query
        try:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", #%s placeholder, avoid sql injection
                (username, email, password_hash)
            )
            conn.commit()

        except Exception as e: #if failed database rollback and return reason
            conn.rollback()
            return "Registration failed. Email may already be in use."
        
        finally: #close cursor and database
            cur.close()
            conn.close()

        return redirect(url_for("login")) #redirect to login 

    return render_template("register.html") #display register page when called

#test
if __name__ == "__main__":
    app.run(debug=True)
