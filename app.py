import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    Amount={}
    return render_template("index.html", load=Amount)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif not request.form.get("confirmation"):
            return apology("must provide second password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("must the same password", 400)

        # Ensure username exists and password is correct
        passwordhash = generate_password_hash(request.form.get(
            "password"), method='scrypt', salt_length=16)
        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                       request.form.get("username"), passwordhash)
        except ValueError:
            return apology("Username already exists", 400)

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route('/autosave', methods=['POST'])
def autosave():
    data = request.json  # Ensure we receive JSON data
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "User not logged in"}), 403

    # Check if user already has an entry
    existing = db.execute("SELECT id FROM depot WHERE id = ?", user_id)

    if existing:
        # Update existing record
        db.execute("""
            UPDATE depot
            SET upgrade1=?, upgrade2=?, upgrade3=?, upgrade4=?, upgrade5=?,
                upgrade6=?, upgrade7=?, upgrade8=?, upgrade9=?, upgrade10=?, amount=?
            WHERE id=?
        """, data["upgrade1"], data["upgrade2"], data["upgrade3"], data["upgrade4"], data["upgrade5"],
           data["upgrade6"], data["upgrade7"], data["upgrade8"], data["upgrade9"], data["upgrade10"],
           data["amount"], user_id)
    else:
        # Insert new record
        db.execute("""
            INSERT INTO depot (id, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5,
                              upgrade6, upgrade7, upgrade8, upgrade9, upgrade10, amount, game1, game2, game3)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, user_id, data["upgrade1"], data["upgrade2"], data["upgrade3"], data["upgrade4"], data["upgrade5"],
           data["upgrade6"], data["upgrade7"], data["upgrade8"], data["upgrade9"], data["upgrade10"],
           data["amount"], 0, 0, 0)

    return jsonify({"message": "Game saved successfully"}), 200  # Ensure response is JSON


@app.route('/load_game', methods=['GET'])
def load_game():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "User not logged in"}), 403

    saved_data = db.execute("SELECT * FROM depot WHERE id = ?", user_id)

    if saved_data:
        return jsonify(saved_data[0])  # CS50 returns a list of dicts, so we get the first element
    else:
        return jsonify({"error": "No saved data found"}), 404


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/ranks", methods=["GET", "POST"])
def ranks():
    user_id = session.get('user_id')
    rows = db.execute("""SELECT users.username, depot.upgrade10, depot.game1 FROM users JOIN depot ON users.id = depot.id ORDER BY depot.upgrade10 DESC;""")
    return render_template("ranks.html", rows=rows)

@app.route("/game1")
@login_required
def game1():
    user_id = session.get('user_id')
    row = db.execute("SELECT game1 FROM depot WHERE id = ?", user_id)

    if row:
        game1 = row[0]["game1"]  # Extract value
    else:
        game1 = 0  # Default high score

    return render_template("game2.html", game1=game1)


@app.route("/game2")
@login_required
def game2():
    return render_template("todo.html")

@app.route("/game3")
@login_required
def game3():
    return render_template("todo.html")

@app.route('/update_high_score', methods=['POST'])
def update_high_score():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 403  # Ensure user is logged in

    data = request.get_json()
    new_high_score = data.get('high_score', 0)

    # Fetch the current high score
    row = db.execute("SELECT game1 FROM depot WHERE id = ?", user_id)

    if row:
        current_high_score = row[0]['game1']

        # Update only if the new score is higher
        if new_high_score > current_high_score:
            db.execute("UPDATE depot SET game1 = ? WHERE id = ?", new_high_score, user_id)
    else:
        # Insert if the user does not exist in depot table
        db.execute("INSERT INTO depot (id, game1) VALUES (?, ?)", user_id, new_high_score)

    return jsonify({"message": "High score updated", "high_score": new_high_score})
