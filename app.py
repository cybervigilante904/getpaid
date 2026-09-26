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
        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>85Spy Trick // Control Terminal</title>

        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }

            body {
                min-height: 100vh;
                background:
                    radial-gradient(
                        circle at center,
                        rgba(0, 255, 120, 0.06),
                        transparent 45%
                    ),
                    #020403;
                color: #00ff88;
                font-family:
                    "Courier New",
                    Courier,
                    monospace;
                overflow-x: hidden;
            }

            body::before {
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                background:
                    repeating-linear-gradient(
                        0deg,
                        rgba(255,255,255,0.025),
                        rgba(255,255,255,0.025) 1px,
                        transparent 1px,
                        transparent 4px
                    );
                z-index: 10;
            }

            body::after {
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                background:
                    radial-gradient(
                        ellipse at center,
                        transparent 45%,
                        rgba(0,0,0,0.75) 100%
                    );
                z-index: 9;
            }

            .terminal {
                width: 100%;
                max-width: 1050px;
                min-height: 100vh;
                margin: auto;
                padding: 35px;
                position: relative;
                z-index: 2;
            }

            .topbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding-bottom: 18px;
                border-bottom:
                    1px solid rgba(0,255,136,0.25);
            }

            .brand {
                font-size: 22px;
                font-weight: bold;
                letter-spacing: 3px;
                text-shadow:
                    0 0 10px rgba(0,255,136,0.8);
            }

            .brand span {
                color: #00bfff;
            }

            .status {
                display: flex;
                align-items: center;
                gap: 9px;
                font-size: 12px;
                letter-spacing: 1px;
            }

            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #00ff88;
                box-shadow:
                    0 0 8px #00ff88,
                    0 0 18px #00ff88;
                animation: blink 1.5s infinite;
            }

            @keyframes blink {
                50% {
                    opacity: 0.35;
                }
            }

            .hero {
                padding-top: 75px;
            }

            .prompt {
                color: #00bfff;
                font-size: 14px;
                margin-bottom: 18px;
            }

            .prompt::before {
                content: "root@85spytick:~$ ";
                color: #00ff88;
            }

            h1 {
                max-width: 850px;
                font-size: clamp(38px, 7vw, 82px);
                line-height: 0.95;
                letter-spacing: -4px;
                text-transform: uppercase;
                text-shadow:
                    0 0 8px rgba(0,255,136,0.7),
                    0 0 30px rgba(0,255,136,0.2);
            }

            h1 span {
                color: #00bfff;
            }

            .description {
                max-width: 650px;
                margin-top: 28px;
                color: #6ee7b7;
                font-size: 15px;
                line-height: 1.8;
            }

            .terminal-box {
                margin-top: 45px;
                border:
                    1px solid rgba(0,255,136,0.22);
                background:
                    rgba(0,20,10,0.55);
                box-shadow:
                    inset 0 0 35px rgba(0,255,136,0.025),
                    0 0 35px rgba(0,255,136,0.04);
            }

            .terminal-header {
                display: flex;
                align-items: center;
                gap: 7px;
                padding: 12px 15px;
                border-bottom:
                    1px solid rgba(0,255,136,0.15);
                color: #4ade80;
                font-size: 11px;
            }

            .terminal-header span {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #00ff88;
            }

            .terminal-content {
                padding: 22px;
                min-height: 155px;
                font-size: 13px;
                line-height: 2;
            }

            .line {
                opacity: 0;
                animation:
                    appear 0.5s forwards;
            }

            .line:nth-child(1) {
                animation-delay: 0.2s;
            }

            .line:nth-child(2) {
                animation-delay: 0.6s;
            }

            .line:nth-child(3) {
                animation-delay: 1s;
            }

            .line:nth-child(4) {
                animation-delay: 1.4s;
            }

            .line:nth-child(5) {
                animation-delay: 1.8s;
            }

            @keyframes appear {
                to {
                    opacity: 1;
                }
            }

            .blue {
                color: #00bfff;
            }

            .dim {
                color: #3f8065;
            }

            .action-area {
                margin-top: 35px;
            }

            button {
                position: relative;
                padding: 17px 28px;
                border:
                    1px solid #00ff88;
                background:
                    rgba(0,255,136,0.05);
                color: #00ff88;
                font-family:
                    "Courier New",
                    Courier,
                    monospace;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
                cursor: pointer;
                text-transform: uppercase;
                transition: 0.2s ease;
                box-shadow:
                    0 0 15px rgba(0,255,136,0.08);
            }

            button:hover {
                background: #00ff88;
                color: #020403;
                box-shadow:
                    0 0 25px rgba(0,255,136,0.45);
            }

            button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            #result {
                display: none;
                margin-top: 30px;
                border:
                    1px solid rgba(0,191,255,0.35);
                background:
                    rgba(0,15,25,0.7);
                padding: 25px;
            }

            .result-title {
                color: #00bfff;
                margin-bottom: 18px;
                font-size: 13px;
                letter-spacing: 2px;
            }

            .link-row {
                margin-top: 15px;
                padding: 14px;
                border-left:
                    2px solid #00ff88;
                background:
                    rgba(0,255,136,0.035);
            }

            .link-label {
                display: block;
                color: #3f8065;
                font-size: 10px;
                margin-bottom: 7px;
                letter-spacing: 1px;
            }

            a {
                color: #00ff88;
                text-decoration: none;
                font-size: 13px;
                word-break: break-all;
            }

            a:hover {
                color: #00bfff;
                text-shadow:
                    0 0 8px rgba(0,191,255,0.7);
            }

            .footer {
                margin-top: 65px;
                padding-top: 18px;
                border-top:
                    1px solid rgba(0,255,136,0.12);
                display: flex;
                justify-content: space-between;
                color: #28523f;
                font-size: 10px;
                letter-spacing: 1px;
            }

            @media (max-width: 600px) {

                .terminal {
                    padding: 22px;
                }

                .topbar {
                    align-items: flex-start;
                    gap: 15px;
                }

                .status {
                    font-size: 9px;
                }

                .hero {
                    padding-top: 55px;
                }

                h1 {
                    letter-spacing: -2px;
                }

                .terminal-content {
                    padding: 16px;
                    font-size: 11px;
                }

                .footer {
                    flex-direction: column;
                    gap: 8px;
                }
            }
        </style>
    </head>

    <body>

        <main class="terminal">

            <header class="topbar">

                <div class="brand">
                    85<span>SPY TICK</span>
                </div>

                <div class="status">
                    <span class="status-dot"></span>
                    SYSTEM ONLINE
                </div>

            </header>


            <section class="hero">

                <div class="prompt">
                    LOCATION_CONTROL_INTERFACE
                </div>

                <h1>
                    LIVE<br>
                    <span>LOCATION</span><br>
                    CONTROL
                </h1>

                <p class="description">
                    85Spy Tick secure location-sharing
                    control interface. Initialize a session
                    and generate a voluntary location-sharing
                    channel.
                </p>


                <div class="terminal-box">

                    <div class="terminal-header">
                        <span></span>
                        <span></span>
                        <span></span>
                        SESSION TERMINAL
                    </div>

                    <div class="terminal-content">

                        <div class="line">
                            <span class="blue">[SYSTEM]</span>
                            Initializing 85Spy Tick...
                        </div>

                        <div class="line">
                            <span class="blue">[NETWORK]</span>
                            Secure channel available.
                        </div>

                        <div class="line">
                            <span class="blue">[GPS]</span>
                            Waiting for authorized device...
                        </div>

                        <div class="line">
                            <span class="blue">[DATABASE]</span>
                            PostgreSQL connection ready.
                        </div>

                        <div class="line dim">
                            $ Awaiting session initialization_
                        </div>

                    </div>

                </div>


                <div class="action-area">

                    <button id="createButton">
                        [ Initialize Session ]
                    </button>

                </div>


                <div id="result">

                    <div class="result-title">
                        // SESSION INITIALIZED
                    </div>

                    <div class="link-row">

                        <span class="link-label">
                            SHARE CHANNEL
                        </span>

                        <a
                            id="shareLink"
                            target="_blank">
                        </a>

                    </div>


                    <div class="link-row">

                        <span class="link-label">
                            CONTROL DASHBOARD
                        </span>

                        <a
                            id="dashboardLink"
                            target="_blank">
                        </a>

                    </div>

                </div>

            </section>


            <footer class="footer">

                <span>
                    85SPY TICK // CONTROL TERMINAL
                </span>

                <span>
                    STATUS: ONLINE
                </span>

            </footer>

        </main>


        <script>

            const createButton =
                document.getElementById(
                    "createButton"
                );

            const result =
                document.getElementById(
                    "result"
                );

            const shareLink =
                document.getElementById(
                    "shareLink"
                );

            const dashboardLink =
                document.getElementById(
                    "dashboardLink"
                );


            createButton.addEventListener(
                "click",
                async () => {

                    createButton.disabled =
                        true;

                    createButton.textContent =
                        "[ INITIALIZING... ]";


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
                            baseUrl +
                            data.share_url;


                        const dashboardUrl =
                            baseUrl +
                            data.dashboard_url;


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


                        createButton.textContent =
                            "[ SESSION ACTIVE ]";


                    } catch (error) {

                        alert(
                            "Unable to initialize session."
                        );


                        createButton.textContent =
                            "[ INITIALIZE SESSION ]";

                    } finally {

                        createButton.disabled =
                            false;

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