import subprocess
import sys
import signal
import os
import time

# List of scripts to run
SCRIPTS = [
    "src/device/audio_monitor.py",
    "src/device/camera_server.py",
    "src/device/environment_monitor.py"
]

processes = []

def signal_handler(sig, frame):
    print("\n🛑  Stopping all services...")
    for p in processes:
        p.terminate()
    sys.exit(0)

def main():
    # Register signal handler for CTRL+C
    signal.signal(signal.SIGINT, signal_handler)

    print("🚀 Starting Baby Monitor Device Services...")
    
    # Get project root (assuming this script is in src/device/)
    # We want to run from the project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(project_root)
    print(f"Working Directory: {project_root}")

    # Environment variables updates (force unbuffered output for real-time logs)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    for script in SCRIPTS:
        try:
            print(f"   ▶️  Launching {script}...")
            p = subprocess.Popen(
                [sys.executable, script],
                env=env,
                cwd=project_root
            )
            processes.append(p)
        except Exception as e:
            print(f"   ❌ Failed to launch {script}: {e}")

    print("\n✅ All services started. Press Ctrl+C to stop.\n")
    print("-" * 50)

    # Keep main process alive to monitor children
    try:
        while True:
            time.sleep(1)
            # Check if any process has died unexpectedy
            for i, p in enumerate(processes):
                if p.poll() is not None:
                    print(f"⚠️  Warning: {SCRIPTS[i]} stopped unexpectedly (Exit Code: {p.returncode})")
                    # Optional: Restart logic could go here
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
