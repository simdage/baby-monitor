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
    try:
        while True:
            buffer = process.stdout.read(65536)
            if not buffer: break
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')
    finally:
        process.terminate()

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/video_feed')
@auth.login_required
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)