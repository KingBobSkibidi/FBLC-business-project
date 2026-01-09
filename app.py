from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "dev-secret-key"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        cur = conn.cursor()
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)
