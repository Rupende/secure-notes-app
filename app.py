import sqlite3
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    g,
)
from werkzeug.security import generate_password_hash, check_password_hash  # [web:6]

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-to-a-strong-random-secret"

# Optional security-related cookie settings for sessions. [web:8]
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ---------- Database helpers ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
    )
    db.commit()


# ---------- Auth utilities ----------

def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


def get_current_user():
    if "user_id" not in session:
        return None
    db = get_db()
    user = db.execute(
        "SELECT id, username, created_at FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()
    return user


# ---------- Routes: Authentication ----------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []

        if not username:
            errors.append("Username is required.")
        if not password:
            errors.append("Password is required.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if not errors:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,),
            ).fetchone()

            if existing:
                errors.append("Username is already taken.")
            else:
                password_hash = generate_password_hash(password)
                db.execute(
                    "INSERT INTO users (username, password_hash, created_at) "
                    "VALUES (?, ?, ?)",
                    (
                        username,
                        password_hash,
                        datetime.utcnow().isoformat(timespec="seconds"),
                    ),
                )
                db.commit()
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("login"))

        for e in errors:
            flash(e, "danger")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------- Routes: Dashboard & Notes ----------

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    db = get_db()
    user = get_current_user()

    # Handle note creation
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not content:
            flash("Both title and content are required.", "danger")
        else:
            db.execute(
                "INSERT INTO notes (user_id, title, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (
                    user["id"],
                    title,
                    content,
                    datetime.utcnow().isoformat(timespec="seconds"),
                ),
            )
            db.commit()
            flash("Note created successfully.", "success")
        return redirect(url_for("dashboard"))

    # Handle search
    query = request.args.get("q", "").strip()
    if query:
        notes = db.execute(
            """
            SELECT id, title, content, created_at
            FROM notes
            WHERE user_id = ?
              AND (title LIKE ? OR content LIKE ?)
            ORDER BY created_at DESC
            """,
            (user["id"], f"%{query}%", f"%{query}%"),
        ).fetchall()
    else:
        notes = db.execute(
            """
            SELECT id, title, content, created_at
            FROM notes
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user["id"],),
        ).fetchall()

    return render_template(
        "dashboard.html",
        user=user,
        notes=notes,
        query=query,
    )


@app.route("/notes/delete/<int:note_id>", methods=["POST"])
@login_required
def delete_note(note_id):
    db = get_db()
    user = get_current_user()

    # Ensure users can delete only their own notes. [web:9]
    note = db.execute(
        "SELECT id FROM notes WHERE id = ? AND user_id = ?",
        (note_id, user["id"]),
    ).fetchone()

    if not note:
        flash("Note not found or unauthorized.", "danger")
        return redirect(url_for("dashboard"))

    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    flash("Note deleted.", "info")
    return redirect(url_for("dashboard"))


# ---------- CLI helper ----------

@app.cli.command("init-db")
def init_db_command():
    """Initialize the database tables."""
    init_db()
    print("Initialized the database.")


if __name__ == "__main__":
    # Ensure DB exists when running directly
    with app.app_context():
        init_db()
    app.run(debug=True)
