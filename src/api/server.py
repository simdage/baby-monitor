import os
import subprocess
import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sys
from dotenv import load_dotenv

load_dotenv()

# Add project root to path to import from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.detection_service import db

app = FastAPI()

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("USER")
    correct_password = os.getenv("PASSWORD")
    if not (secrets.compare_digest(credentials.username, correct_username) and
            secrets.compare_digest(credentials.password, correct_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def generate_frames():
    # Using the rpicam command
    command = ["rpicam-vid", "-t", "0", "--inline", "--width", "640", "--height", "480", "--codec", "mjpeg", "-o", "-"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=0)
    
    buffer = b''
    try:
        while True:
            data = process.stdout.read(4096)
            if not data:
                break
            buffer += data
            
            while True:
                start = buffer.find(b'\xff\xd8')
                end = buffer.find(b'\xff\xd9')
                
                if start != -1 and end != -1:
                    if start < end:
                        jpg = buffer[start:end+2]
                        buffer = buffer[end+2:]
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')
                    else:
                        buffer = buffer[start:]
                else:
                    break
    finally:
        process.terminate()

@app.get("/video_feed")
def video_feed(username: str = Depends(get_current_username)):
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/history")
def get_history():
    """Fetch recent predictions from BigQuery."""
    try:
        # data is list of tuples: (timestamp, probability, is_cry, gcs_uri)
        data = db.get_recent_predictions_bigquery(limit=100)
        
        # Convert to JSON friendly format
        result = []
        for row in data:
            result.append({
                "timestamp": row[0],
                "probability": row[1],
                "is_cry": row[2],
                "gcs_uri": row[3]
            })
        return result
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []

class LogEventRequest(BaseModel):
    event_type: str
    notes: str
    timestamp: str # ISO string 
    intensity: str

@app.post("/api/log")
def log_event(event: LogEventRequest):
    """Log a manual event."""
    success = db.log_manual_event_bigquery(
        event_type=event.event_type,
        notes=event.notes,
        timestamp_iso=event.timestamp,
        intensity=event.intensity
    )
    
    if success:
        return {"status": "success"}
    else:
        return {"status": "error", "message": "Failed to log event"}, 500

@app.get("/api/logs")
def get_logs():
    """Fetch manual logs."""
    return db.get_manual_logs_bigquery()

# Mount static files - this will serve the built React app
# We only do this if the directory exists (it will in Docker)
static_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist')
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
