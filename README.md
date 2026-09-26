# LiveHook

LiveHook is a consent-based live location-sharing web application that allows a person to voluntarily share their real-time GPS location through a browser.

The application uses browser geolocation, a Flask backend, PostgreSQL, and Leaflet to display the shared location on a live map.

## Features

* Create unique location-sharing sessions
* Generate a shareable location URL
* Request location permission directly from the user's browser
* Continuously receive GPS coordinates using browser geolocation
* Store location data in PostgreSQL
* Display the latest location on an interactive map
* Automatically update the map every 2 seconds
* Show latitude, longitude, and location accuracy
* Deployable as a Flask web service

## How It Works

```text
Session Creator
      |
      v
Create Session
      |
      v
Unique Share Link
      |
      v
Person Opens Share Link
      |
      v
Clicks "Share My Location"
      |
      v
Browser Requests GPS Permission
      |
      v
Browser Sends Coordinates
      |
      v
Flask API
      |
      v
PostgreSQL
      |
      v
Dashboard
      |
      v
Live Leaflet Map
```

Location sharing only begins after the user explicitly chooses to share their location and grants browser permission.

## Technology Stack

### Frontend

* HTML
* CSS
* JavaScript
* Leaflet.js
* OpenStreetMap

### Backend

* Python
* Flask
* Gunicorn

### Database

* PostgreSQL
* Psycopg

### Deployment

* Render

## Project Structure

```text
LiveHook/
│
├── app.py
├── requirements.txt
│
└── templates/
    ├── share.html
    └── dashboard.html
```

## API Endpoints

### Create a Session

```http
POST /api/sessions
```

Creates a new location-sharing session.

Example response:

```json
{
    "session_id": "example-session-id",
    "share_url": "/share/example-session-id",
    "dashboard_url": "/dashboard/example-session-id"
}
```

### Share Location

```http
POST /api/location/<session_id>
```

Receives the user's location.

Example request:

```json
{
    "latitude": -17.8252,
    "longitude": 31.0335,
    "accuracy": 10.5
}
```

### Get Latest Location

```http
GET /api/location/<session_id>
```

Returns the latest location stored for the session.

Example response:

```json
{
    "location": {
        "latitude": -17.8252,
        "longitude": 31.0335,
        "accuracy": 10.5,
        "created_at": "2026-09-26T12:00:00+00:00"
    }
}
```

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/cybervigilante904/tricklocation.git
cd tricklocation
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Set the `DATABASE_URL` environment variable.

Windows PowerShell:

```powershell
$env:DATABASE_URL="your-postgresql-connection-string"
```

Linux/macOS:

```bash
export DATABASE_URL="your-postgresql-connection-string"
```

### 5. Start the application

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

## Production

The application can be started with Gunicorn:

```bash
gunicorn app:app
```

The production deployment is hosted on Render.

## Location Sharing Flow

### Step 1

Create a session using:

```http
POST /api/sessions
```

### Step 2

Send the generated share URL to the person who wants to share their location.

### Step 3

The person opens the share page.

### Step 4

They click:

```text
Share My Location
```

### Step 5

The browser asks for location permission.

### Step 6

After permission is granted, the browser sends GPS coordinates to the Flask API.

### Step 7

The dashboard retrieves the latest coordinates and updates the map.

## Privacy & Consent

LiveHook is designed around explicit user consent.

The application does not:

* Track people secretly
* Track a phone number by itself
* Bypass browser location permissions
* Install tracking software
* Access GPS without user permission
* Provide covert surveillance functionality

The person sharing their location must explicitly open the sharing page, choose to share their location, and grant browser permission.

## Database

LiveHook uses two PostgreSQL tables.

### sessions

Stores location-sharing sessions.

```text
id
session_id
created_at
```

### locations

Stores location updates.

```text
id
session_id
latitude
longitude
accuracy
created_at
```

## Future Improvements

Possible improvements include:

* Stop sharing button
* Session expiration
* Automatic session cleanup
* Authentication
* Better dashboard UI
* Real-time WebSocket updates
* Location history
* Accuracy circle on the map
* Multiple participants
* Session management
* Rate limiting
* Improved privacy controls
* Mobile-friendly dashboard
* Automatic sharing status indicators

## License

This project is provided for learning and development purposes.

Use location-sharing functionality responsibly and only with the knowledge and consent of the person sharing their location.

## Author

**Blessing Ngoni Mujere**

Full Stack Developer & Software Engineer

Building practical software solutions using modern frontend, backend, and intelligent application technologies.
-also interested in cybersecurity 
