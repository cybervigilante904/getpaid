import os
import secrets

from flask import Flask, request, jsonify, render_template, abort, Response
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

import psycopg
from psycopg.rows import dict_row


app = Flask(__name__)

CORS(app)

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1
)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

MAX_FILE_SIZE = 10 * 1024 * 1024


def get_db_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


def initialize_database():

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                ALTER TABLE sessions
                ADD COLUMN IF NOT EXISTS session_id TEXT
                """
            )

            cur.execute(
                """
                ALTER TABLE sessions
                ALTER COLUMN session_id DROP NOT NULL
                """
            )

            cur.execute(
                """
                ALTER TABLE sessions
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
                """
            )

            cur.execute(
                """
                ALTER TABLE sessions
                ALTER COLUMN created_at
                SET DEFAULT CURRENT_TIMESTAMP
                """
            )

            cur.execute(
                """
                ALTER TABLE sessions
                ALTER COLUMN created_at DROP NOT NULL
                """
            )

            cur.execute(
                """
                ALTER TABLE sessions
                ALTER COLUMN id TYPE TEXT
                USING id::TEXT
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS locations (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    latitude DOUBLE PRECISION NOT NULL,
                    longitude DOUBLE PRECISION NOT NULL,
                    accuracy DOUBLE PRECISION,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT
                )
                """
            )

            cur.execute(
                """
                ALTER TABLE locations
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
                """
            )

            cur.execute(
                """
                ALTER TABLE locations
                ALTER COLUMN created_at
                SET DEFAULT CURRENT_TIMESTAMP
                """
            )

            cur.execute(
                """
                ALTER TABLE locations
                ALTER COLUMN created_at DROP NOT NULL
                """
            )

            cur.execute(
                """
                ALTER TABLE locations
                ALTER COLUMN session_id TYPE TEXT
                USING session_id::TEXT
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS device_info (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_agent TEXT,
                    platform TEXT,
                    browser TEXT,
                    operating_system TEXT,
                    device_type TEXT,
                    language TEXT,
                    timezone TEXT,
                    screen_width INTEGER,
                    screen_height INTEGER,
                    pixel_ratio DOUBLE PRECISION,
                    cpu_cores INTEGER,
                    device_memory DOUBLE PRECISION,
                    touch_points INTEGER,
                    online BOOLEAN,
                    mobile BOOLEAN,
                    connection_type TEXT,
                    effective_connection_type TEXT,
                    downlink DOUBLE PRECISION,
                    rtt INTEGER,
                    save_data BOOLEAN,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                ALTER TABLE device_info
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
                """
            )

            cur.execute(
                """
                ALTER TABLE device_info
                ALTER COLUMN created_at
                SET DEFAULT CURRENT_TIMESTAMP
                """
            )

            cur.execute(
                """
                ALTER TABLE device_info
                ALTER COLUMN created_at DROP NOT NULL
                """
            )

            cur.execute(
                """
                ALTER TABLE device_info
                ALTER COLUMN session_id TYPE TEXT
                USING session_id::TEXT
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS uploads (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_data BYTEA NOT NULL,
                    file_size INTEGER NOT NULL,
                    content_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                ALTER TABLE uploads
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
                """
            )

            cur.execute(
                """
                ALTER TABLE uploads
                ALTER COLUMN created_at
                SET DEFAULT CURRENT_TIMESTAMP
                """
            )

            cur.execute(
                """
                ALTER TABLE uploads
                ALTER COLUMN created_at DROP NOT NULL
                """
            )

            cur.execute(
                """
                ALTER TABLE uploads
                ALTER COLUMN session_id TYPE TEXT
                USING session_id::TEXT
                """
            )

        conn.commit()

    finally:

        conn.close()


def session_exists(session_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM sessions
                WHERE id = %s
                """,
                (session_id,)
            )

            return cur.fetchone() is not None

    finally:

        conn.close()


@app.route("/")
def home():

    return render_template(
        "home.html"
    )


@app.route("/share/<session_id>")
def share(session_id):

    if not session_exists(session_id):
        abort(404)

    return render_template(
        "share.html",
        session_id=session_id
    )


@app.route("/dashboard/<session_id>")
def dashboard(session_id):

    if not session_exists(session_id):
        abort(404)

    return render_template(
        "dashboard.html",
        session_id=session_id
    )


@app.route("/api/sessions", methods=["POST"])
def create_session():

    session_id = secrets.token_urlsafe(16)

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO sessions (
                    id,
                    created_at
                )
                VALUES (
                    %s,
                    CURRENT_TIMESTAMP
                )
                """,
                (session_id,)
            )

        conn.commit()

    finally:

        conn.close()

    base_url = request.url_root.rstrip("/")

    share_url = (
        f"{base_url}/share/{session_id}"
    )

    dashboard_url = (
        f"{base_url}/dashboard/{session_id}"
    )

    return jsonify({
        "success": True,
        "session_id": session_id,
        "share_url": share_url,
        "dashboard_url": dashboard_url
    })


@app.route(
    "/api/location/<session_id>",
    methods=["POST", "GET"]
)
def location(session_id):

    if not session_exists(session_id):
        return jsonify({
            "success": False,
            "error": "Session not found."
        }), 404

    conn = get_db_connection()

    try:

        if request.method == "POST":

            data = request.get_json(
                silent=True
            ) or {}

            latitude = data.get("latitude")
            longitude = data.get("longitude")
            accuracy = data.get("accuracy")

            if latitude is None or longitude is None:

                return jsonify({
                    "success": False,
                    "error": "Latitude and longitude are required."
                }), 400

            try:

                latitude = float(latitude)
                longitude = float(longitude)

                if accuracy is not None:
                    accuracy = float(accuracy)

            except (TypeError, ValueError):

                return jsonify({
                    "success": False,
                    "error": "Invalid location values."
                }), 400

            if not -90 <= latitude <= 90:

                return jsonify({
                    "success": False,
                    "error": "Invalid latitude."
                }), 400

            if not -180 <= longitude <= 180:

                return jsonify({
                    "success": False,
                    "error": "Invalid longitude."
                }), 400

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO locations (
                        session_id,
                        latitude,
                        longitude,
                        accuracy,
                        created_at,
                        ip_address
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        CURRENT_TIMESTAMP,
                        %s
                    )
                    """,
                    (
                        session_id,
                        latitude,
                        longitude,
                        accuracy,
                        request.remote_addr
                    )
                )

            conn.commit()

            return jsonify({
                "success": True
            })

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    session_id,
                    latitude,
                    longitude,
                    accuracy,
                    created_at,
                    ip_address
                FROM locations
                WHERE session_id = %s
                ORDER BY id DESC
                LIMIT 100
                """,
                (session_id,)
            )

            locations = cur.fetchall()

        return jsonify({
            "success": True,
            "locations": locations
        })

    finally:

        conn.close()


@app.route(
    "/api/device-info/<session_id>",
    methods=["POST", "GET"]
)
def device_info(session_id):

    if not session_exists(session_id):
        return jsonify({
            "success": False,
            "error": "Session not found."
        }), 404

    conn = get_db_connection()

    try:

        if request.method == "POST":

            data = request.get_json(
                silent=True
            ) or {}

            connection = data.get(
                "connection",
                {}
            )

            if not isinstance(connection, dict):
                connection = {}

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO device_info (
                        session_id,
                        user_agent,
                        platform,
                        browser,
                        operating_system,
                        device_type,
                        language,
                        timezone,
                        screen_width,
                        screen_height,
                        pixel_ratio,
                        cpu_cores,
                        device_memory,
                        touch_points,
                        online,
                        mobile,
                        connection_type,
                        effective_connection_type,
                        downlink,
                        rtt,
                        save_data,
                        ip_address,
                        created_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        CURRENT_TIMESTAMP
                    )
                    """,
                    (
                        session_id,
                        data.get("user_agent"),
                        data.get("platform"),
                        data.get("browser"),
                        data.get("operating_system"),
                        data.get("device_type"),
                        data.get("language"),
                        data.get("timezone"),
                        data.get("screen_width"),
                        data.get("screen_height"),
                        data.get("pixel_ratio"),
                        data.get("cpu_cores"),
                        data.get("device_memory"),
                        data.get("touch_points"),
                        data.get("online"),
                        data.get("mobile"),
                        connection.get("type"),
                        connection.get("effective_type"),
                        connection.get("downlink"),
                        connection.get("rtt"),
                        connection.get("save_data"),
                        request.remote_addr
                    )
                )

            conn.commit()

            return jsonify({
                "success": True
            })

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    session_id,
                    user_agent,
                    platform,
                    browser,
                    operating_system,
                    device_type,
                    language,
                    timezone,
                    screen_width,
                    screen_height,
                    pixel_ratio,
                    cpu_cores,
                    device_memory,
                    touch_points,
                    online,
                    mobile,
                    connection_type,
                    effective_connection_type,
                    downlink,
                    rtt,
                    save_data,
                    ip_address,
                    created_at
                FROM device_info
                WHERE session_id = %s
                ORDER BY id DESC
                LIMIT 20
                """,
                (session_id,)
            )

            devices = cur.fetchall()

        return jsonify({
            "success": True,
            "device_info": devices
        })

    finally:

        conn.close()


@app.route(
    "/api/upload/<session_id>",
    methods=["POST"]
)
def upload_file(session_id):

    if not session_exists(session_id):
        return jsonify({
            "success": False,
            "error": "Session not found."
        }), 404

    if "file" not in request.files:

        return jsonify({
            "success": False,
            "error": "No file provided."
        }), 400

    file = request.files["file"]

    if not file.filename:

        return jsonify({
            "success": False,
            "error": "No filename provided."
        }), 400

    file_data = file.read()

    if len(file_data) > MAX_FILE_SIZE:

        return jsonify({
            "success": False,
            "error": "File exceeds 10 MB limit."
        }), 413

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO uploads (
                    session_id,
                    filename,
                    file_data,
                    file_size,
                    content_type,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP
                )
                """,
                (
                    session_id,
                    file.filename,
                    file_data,
                    len(file_data),
                    file.content_type
                )
            )

            upload_id = cur.fetchone()

        conn.commit()

        return jsonify({
            "success": True,
            "upload_id": upload_id
        })

    finally:

        conn.close()


@app.route(
    "/api/uploads/<session_id>",
    methods=["GET"]
)
def get_uploads(session_id):

    if not session_exists(session_id):
        return jsonify({
            "success": False,
            "error": "Session not found."
        }), 404

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    filename,
                    file_size,
                    content_type,
                    created_at
                FROM uploads
                WHERE session_id = %s
                ORDER BY id DESC
                """,
                (session_id,)
            )

            uploads = cur.fetchall()

        for upload in uploads:

            upload["url"] = (
                f"/uploads/{upload['id']}"
            )

        return jsonify(uploads)

    finally:

        conn.close()


@app.route(
    "/uploads/<int:upload_id>",
    methods=["GET"]
)
def serve_upload(upload_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    filename,
                    file_data,
                    content_type
                FROM uploads
                WHERE id = %s
                """,
                (upload_id,)
            )

            upload = cur.fetchone()

        if not upload:
            abort(404)

        return Response(
            upload["file_data"],
            mimetype=upload["content_type"]
                or "application/octet-stream",
            headers={
                "Content-Disposition":
                    f'inline; filename="{upload["filename"]}"'
            }
        )

    finally:

        conn.close()


@app.route(
    "/api/session/<session_id>",
    methods=["GET"]
)
def get_session(session_id):

    if not session_exists(session_id):
        return jsonify({
            "success": False,
            "error": "Session not found."
        }), 404

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    created_at
                FROM sessions
                WHERE id = %s
                """,
                (session_id,)
            )

            session = cur.fetchone()

            cur.execute(
                """
                SELECT
                    id,
                    session_id,
                    latitude,
                    longitude,
                    accuracy,
                    created_at,
                    ip_address
                FROM locations
                WHERE session_id = %s
                ORDER BY id DESC
                LIMIT 100
                """,
                (session_id,)
            )

            locations = cur.fetchall()

            cur.execute(
                """
                SELECT
                    id,
                    session_id,
                    user_agent,
                    platform,
                    browser,
                    operating_system,
                    device_type,
                    language,
                    timezone,
                    screen_width,
                    screen_height,
                    pixel_ratio,
                    cpu_cores,
                    device_memory,
                    touch_points,
                    online,
                    mobile,
                    connection_type,
                    effective_connection_type,
                    downlink,
                    rtt,
                    save_data,
                    ip_address,
                    created_at
                FROM device_info
                WHERE session_id = %s
                ORDER BY id DESC
                LIMIT 20
                """,
                (session_id,)
            )

            devices = cur.fetchall()

        return jsonify({
            "success": True,
            "session": session,
            "locations": locations,
            "device_info": devices
        })

    finally:

        conn.close()


initialize_database()


if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )