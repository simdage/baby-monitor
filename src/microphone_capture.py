#!/usr/bin/env python3
"""
Microphone capture script that reads audio input and prints raw bytes.
"""

import pyaudio
import sys

# Audio configuration
CHUNK = 1024  # Number of frames per buffer
FORMAT = pyaudio.paInt16  # 16-bit samples
CHANNELS = 1  # Mono audio
RATE = 44100  # Sample rate (Hz)

def capture_microphone():
    """Capture audio from microphone and print raw bytes."""
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
        
        print(f"Recording started. Sample rate: {RATE} Hz, Chunk size: {CHUNK} frames", file=sys.stderr)
        print("Raw audio bytes (press Ctrl+C to stop):", file=sys.stderr)
        print("-" * 50, file=sys.stderr)
        
        try:
            while True:
                # Read audio data
                data = stream.read(CHUNK, exception_on_overflow=False)
                
                # Print raw bytes
                # Option 1: Print as hex representation
                print(data.hex())
                
                # Option 2: Uncomment below to print as raw bytes (may not display well in terminal)
                # sys.stdout.buffer.write(data)
                # sys.stdout.flush()
                
        except KeyboardInterrupt:
            print("\nStopping capture...", file=sys.stderr)
        finally:
            stream.stop_stream()
            stream.close()
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        audio.terminate()

if __name__ == "__main__":
    capture_microphone()

