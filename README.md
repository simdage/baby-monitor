# baby-monitor
Detecting infant crying on remote device using ML for instant notifications

## Running with Docker

### Audio Access Setup

Docker containers need special configuration to access audio devices. Choose the method that works for your system:

#### Option 1: PulseAudio (Recommended for macOS/Linux)

**For macOS:**
```bash
# Install PulseAudio on macOS (if not already installed)
brew install pulseaudio

# Start PulseAudio server
pulseaudio --load=module-native-protocol-tcp --exit-idle-time=-1 --daemon

# Run the container with PulseAudio socket
docker run -it --rm \
  -v /tmp/pulse-socket:/tmp/pulse-socket \
  -e PULSE_SERVER=unix:/tmp/pulse-socket \
  -e PULSE_COOKIE=/tmp/pulse-cookie \
  -v ~/.config/pulse:/root/.config/pulse \
  <image-id>
```

**For Linux:**
```bash
# Run the container with PulseAudio socket
docker run -it --rm \
  -v /run/user/$(id -u)/pulse:/run/user/1000/pulse \
  -e PULSE_SERVER=unix:/run/user/1000/pulse/native \
  <image-id>
```

#### Option 2: ALSA Direct Access (Linux only)

```bash
# Run with ALSA device access
docker run -it --rm \
  --device /dev/snd \
  -e ALSA_CARD=0 \
  <image-id>
```

#### Option 3: Using Docker Compose

Create a `docker-compose.yml` file with the appropriate audio configuration for your system.
