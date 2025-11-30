import os
import sys
import time
import requests
import numpy as np
import torch
import pyaudio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path to allow imports from src
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

from src.model.train_model import CryClassifier

# Configuration
SAMPLE_RATE = 16000
WINDOW_DURATION = 7  # seconds
WINDOW_SAMPLES = SAMPLE_RATE * WINDOW_DURATION  # 112000 samples
CHUNK_SIZE = 4000  # Process in smaller chunks for responsiveness
MODEL_PATH = os.path.join(project_root, "src/model/checkpoints/best_model.pt")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Alert Configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
ALERT_COOLDOWN = 60  # seconds
last_alert_time = 0

def send_slack_alert(probability):
    """Send a Slack notification if configured."""
    global last_alert_time
    
    if not SLACK_WEBHOOK_URL:
        return
        
    current_time = time.time()
    if current_time - last_alert_time < ALERT_COOLDOWN:
        return
        
    try:
        message = f"👶 Baby Crying Detected! Probability: {probability:.2f}"
        payload = {"text": message}
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"\n[Alert Sent] {message}")
        last_alert_time = current_time
    except Exception as e:
        print(f"\n[Alert Failed] {e}")

def load_model():
    try:
        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
        model = CryClassifier().to(DEVICE)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

def predict_cry(model, audio_buffer):
    waveform = torch.from_numpy(audio_buffer).float().to(DEVICE)
    
    # Normalize if needed (though PyAudio float32 is usually -1 to 1)
    if waveform.abs().max() > 1.0:
         waveform = waveform / waveform.abs().max()
    
    input_tensor = waveform.unsqueeze(0).unsqueeze(0)
    
    # Inference
    with torch.no_grad():
        outputs = model(input_tensor)
        probs = torch.softmax(outputs, dim=1)
        cry_prob = probs[0][1].item()
    
    return cry_prob


def main():
    print(f"Loading model from {MODEL_PATH}...")
    
    if not SLACK_WEBHOOK_URL:
        print("⚠️  SLACK_WEBHOOK_URL not set. Alerts will be disabled.")
    else:
        print("✅ Slack alerts enabled.")
    
    # Load model
    model = load_model()
    
    # Audio buffer
    audio_buffer = np.zeros(WINDOW_SAMPLES, dtype=np.float32)
    
    # PyAudio Setup
    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK_SIZE)
        
        print(f"\n🎤 Listening... (Buffer filling: {WINDOW_DURATION}s)")
        print("Press Ctrl+C to stop")
        
        buffer_filled = False
        samples_collected = 0
        
        while True:
            # Read audio chunk
            try:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                chunk = np.frombuffer(data, dtype=np.float32)
                
                # Update buffer (sliding window)
                audio_buffer = np.roll(audio_buffer, -len(chunk))
                audio_buffer[-len(chunk):] = chunk
                
                samples_collected += len(chunk)
                
                if not buffer_filled:
                    if samples_collected >= WINDOW_SAMPLES:
                        buffer_filled = True
                        print("Buffer full, starting predictions...")
                    else:
                        progress = min(100, int(100 * samples_collected / WINDOW_SAMPLES))
                        print(f"Filling buffer: {progress}%", end='\r')
                        continue
                
                cry_prob = predict_cry(model, audio_buffer)
                
                # Output result
                if cry_prob > 0.5:
                    print(f"\033[91m👶 BABY CRYING! Probability: {cry_prob:.2f}\033[0m")
                    send_slack_alert(cry_prob)
                else:
                    print(f"Normal ({cry_prob:.2f})", end='\r')
                    
            except IOError as e:
                print(f"Audio error: {e}")
                continue
                
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()

if __name__ == "__main__":
    main()