from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "dev-secret-key"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

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
            return redirect(url_for("profile"))

        return "Invalid email or password" #incorrect login
    
    return render_template("login.html") #display login page when called

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
            return f"Registration failed: {e}"
        
        finally: #close cursor and database
            cur.close()
            conn.close()

        return redirect(url_for("login")) #redirect to login 

    return render_template("register.html") #display register page when called

if __name__ == "__main__":
    app.run(debug=True)
