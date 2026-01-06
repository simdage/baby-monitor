from flask import Flask, Response, render_template
from flask_httpauth import HTTPBasicAuth
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, template_folder='.')
auth = HTTPBasicAuth()

# --- CONFIGURATION ---
USER_DATA = {
    os.getenv("USER"): os.getenv("PASSWORD")
}

@auth.verify_password
def verify(username, password):
    if username in USER_DATA and USER_DATA.get(username) == password:
        return username

def generate_frames():
    # Using the rpicam command we verified earlier
    command = ["rpicam-vid", "-t", "0", "--inline", "--width", "640", "--height", "480", "--codec", "mjpeg", "-o", "-"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=0)
    
    buffer = b''
    try:
        while True:
            # Read a chunk of data
            data = process.stdout.read(4096)
            if not data:
                break
            buffer += data
            
            # Look for the start and end of the JPEG frame
            while True:
                start = buffer.find(b'\xff\xd8')
                end = buffer.find(b'\xff\xd9')
                
                if start != -1 and end != -1:
                    if start < end:
                        # We have a full frame
                        jpg = buffer[start:end+2]
                        buffer = buffer[end+2:] # Remove the frame from the buffer
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')
                    else:
                        # The end marker appeared before the start marker, discard the garbage at the beginning
                        buffer = buffer[start:]
                else:
                    # We don't have a full frame yet, need to read more data
                    break
                    
    finally:
        process.terminate()

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)