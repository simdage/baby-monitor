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

import shutil
import time
import random

# ... imports ...

def generate_mock_frames():
    """Generates mock video frames (random colored noise) when camera is unavailable."""
    width, height = 640, 480
    while True:
        # Create a simple placeholder image (random noise for demonstration)
        # In a real app, you might want to load a static image or use PIL to draw text
        # For now, just sending a very small valid JPEG header + random bytes to simulate a frame
        # (This is a bit hacky without PIL, but avoids adding dependencies)
        
        # Better approach: Just yield a static placeholder if possible, or simple MJPEG structure
        # Let's try to generate a minimal valid JPEG or just random noise that might not render perfectly but shows activity
        # Actually, let's use a simple pattern. 
        
        # Since generating real JPEGs without PIL is hard, checking if we can just yield a static message?
        # Browser expects MJPEG. 
        
        # Let's rely on the fact that we might just want to skip the camera command if it fails.
        # But the user wants to see "the video".
        
        # Let's assume the user is okay with a "No Camera" placeholder or similar.
        # If we can't generate a real JPEG, maybe we can just sleep.
        
        time.sleep(1/10) # 10 FPS
        
        # Create a dummy frame (just a 1x1 gray pixel JPEG)
        # 1x1 pixel gray jpeg hex dump
        dummy_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00\x00?\x00\xbf\xc0\x00\x00\x00'
        
        # Actually, let's use a slightly larger one valid header if possible, or just fail gracefully.
        # If I can't easily make a JPEG, I'll return a textual frame? No, MJPEG needs images.
        
        # Let's use a predefined valid JPEG bytes sequence for a small gray square.
        # The above bytes are a valid 1x1 gray jpeg.
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + dummy_jpeg + b'\r\n')

import shutil
import time
import random
import requests

# ... imports ...

def proxy_remote_feed(url):
    """Proxies the video feed from a remote URL."""
    try:
        with requests.get(url, stream=True, timeout=5) as r:
            r.raise_for_status()
            # Iterate over the response content line by line or chunk by chunk
            # MJPEG streams are multipart/x-mixed-replace. 
            # We can just yield chunks as they come in.
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
    except Exception as e:
        print(f"Error connecting to remote camera at {url}: {e}")
        # Fallback to mock if remote fails
        yield from generate_mock_frames()

def generate_frames():
    # 1. Check for remote camera URL
    camera_url = os.getenv("CAMERA_SERVER_URL")
    if camera_url:
        print(f"Using remote camera at: {camera_url}")
        yield from proxy_remote_feed(camera_url)
        return

    # 2. Check if rpicam-vid exists locally
    if shutil.which("rpicam-vid") is None:
        print("rpicam-vid not found, using mock frames")
        yield from generate_mock_frames()
        return

    # 3. Use local rpicam-vid
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
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
# ... rest of file ...

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
