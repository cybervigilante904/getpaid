import os
import secrets
from datetime import datetime, timezone

import psycopg
from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set.")

    return psycopg.connect(DATABASE_URL)


def initialize_database():
    connection = get_db()

    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                session_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,
                accuracy DOUBLE PRECISION,
                created_at TIMESTAMPTZ NOT NULL
            )
        """)

    connection.commit()
    connection.close()


def session_exists(session_id):
    connection = get_db()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT session_id
            FROM sessions
            WHERE session_id = %s
            """,
            (session_id,)
        )

        session = cursor.fetchone()

    connection.close()

    return session is not None


@app.route("/")
def home():
    return """
    <h1>LiveHook</h1>
    <p>Consent-based live location sharing.</p>
    <p>Use POST /api/sessions to create a tracking session.</p>
    """


@app.route("/api/sessions", methods=["POST"])
def create_session():
    session_id = secrets.token_urlsafe(24)

    connection = get_db()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO sessions (
                session_id,
                created_at
            )
            VALUES (%s, %s)
            """,
            (
                session_id,
                datetime.now(timezone.utc)
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

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO locations (
                session_id,
                latitude,
                longitude,
                accuracy,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                session_id,
                latitude,
                longitude,
                accuracy,
                datetime.now(timezone.utc)
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

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                latitude,
                longitude,
                accuracy,
                created_at
            FROM locations
            WHERE session_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id,)
        )

        location = cursor.fetchone()

    connection.close()

    if location is None:
        return jsonify({
            "location": None
        })

    return jsonify({
        "location": {
            "latitude": location[0],
            "longitude": location[1],
            "accuracy": location[2],
            "created_at": location[3].isoformat()
        }
    })


initialize_database()