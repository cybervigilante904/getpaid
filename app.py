import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

# Render persistent disk location
DATABASE = Path("/var/data/tracelink.db")


def get_db():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            accuracy REAL,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def session_exists(session_id):
    connection = get_db()

    session = connection.execute(
        "SELECT session_id FROM sessions WHERE session_id = ?",
        (session_id,)
    ).fetchone()

    connection.close()

    return session is not None


@app.route("/")
def home():
    return """
    <h1>TraceLink</h1>
    <p>Consent-based live location sharing.</p>
    <p>Use POST /api/sessions to create a tracking session.</p>
    """


@app.route("/api/sessions", methods=["POST"])
def create_session():
    session_id = secrets.token_urlsafe(24)

    connection = get_db()

    connection.execute(
        """
        INSERT INTO sessions (session_id, created_at)
        VALUES (?, ?)
        """,
        (
            session_id,
            datetime.now(timezone.utc).isoformat()
        )
    )

    connection.commit()
    connection.close()

    return jsonify({
        "session_id": session_id,
        "share_url": f"/share/{session_id}",
        "dashboard_url": f"/dashboard/{session_id}"
    })


@app.route("/share/<session_id>")
def share_page(session_id):
    if not session_exists(session_id):
        return "Session not found.", 404

    return render_template(
        "share.html",
        session_id=session_id
    )


@app.route("/dashboard/<session_id>")
def dashboard_page(session_id):
    if not session_exists(session_id):
        return "Session not found.", 404

    return render_template(
        "dashboard.html",
        session_id=session_id
    )


@app.route("/api/location/<session_id>", methods=["POST"])
def update_location(session_id):

    if not session_exists(session_id):
        return jsonify({
            "error": "Session not found"
        }), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "JSON data is required"
        }), 400

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])

        accuracy = data.get("accuracy")

        if accuracy is not None:
            accuracy = float(accuracy)

    except (KeyError, TypeError, ValueError):
        return jsonify({
            "error": "Invalid location data"
        }), 400

    if not -90 <= latitude <= 90:
        return jsonify({
            "error": "Invalid latitude"
        }), 400

    if not -180 <= longitude <= 180:
        return jsonify({
            "error": "Invalid longitude"
        }), 400

    connection = get_db()

    connection.execute(
        """
        INSERT INTO locations (
            session_id,
            latitude,
            longitude,
            accuracy,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session_id,
            latitude,
            longitude,
            accuracy,
            datetime.now(timezone.utc).isoformat()
        )
    )

    connection.commit()
    connection.close()

    return jsonify({
        "success": True
    })


@app.route("/api/location/<session_id>", methods=["GET"])
def get_location(session_id):

    if not session_exists(session_id):
        return jsonify({
            "error": "Session not found"
        }), 404

    connection = get_db()

    location = connection.execute(
        """
        SELECT latitude, longitude, accuracy, created_at
        FROM locations
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (session_id,)
    ).fetchone()

    connection.close()

    if location is None:
        return jsonify({
            "location": None
        })

    return jsonify({
        "location": {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "accuracy": location["accuracy"],
            "created_at": location["created_at"]
        }
    })


# Initialize database when the application starts
initialize_database()