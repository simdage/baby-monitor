#!/usr/bin/env python3
"""
Microphone capture script that records audio for 10 seconds and saves it to a file.
"""

import pyaudio
import wave
import sys
import time

# Audio configuration
CHUNK = 1024  # Number of frames per buffer
FORMAT = pyaudio.paInt16  # 16-bit samples
CHANNELS = 1  # Mono audio
RATE = 44100  # Sample rate (Hz)
RECORD_SECONDS = 10  # Duration of recording
OUTPUT_FILENAME = "recording.wav"  # Output file name

def capture_microphone():
    """Capture audio from microphone for 10 seconds and save to a WAV file."""
    audio = pyaudio.PyAudio()
    
    try:
        # List available input devices (optional, for debugging)
        print("Available input devices:", file=sys.stderr)
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  Device {i}: {info['name']}", file=sys.stderr)
        print(file=sys.stderr)
        
        # Open audio stream
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        print(f"Recording for {RECORD_SECONDS} seconds...", file=sys.stderr)
        print(f"Sample rate: {RATE} Hz, Chunk size: {CHUNK} frames", file=sys.stderr)
        
        # Calculate number of chunks needed
        num_chunks = int(RATE / CHUNK * RECORD_SECONDS)
        frames = []
        
        # Record audio
        for i in range(num_chunks):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            # Show progress
            elapsed = (i + 1) * CHUNK / RATE
            print(f"\rRecording... {elapsed:.1f}s / {RECORD_SECONDS}s", end="", file=sys.stderr)
        
        print("\nRecording complete. Saving to file...", file=sys.stderr)
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        # Save to WAV file
        with wave.open(OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        
        print(f"Audio saved to: {OUTPUT_FILENAME}", file=sys.stderr)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        audio.terminate()

if __name__ == "__main__":
    capture_microphone()

