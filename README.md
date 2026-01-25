# Baby Cry Monitoring AIoT System

A comprehensive AI-powered baby monitoring system that combines real-time edge AI, cloud analytics, and a modern web interface.

## System Architecture

The system is composed of three main layers:

1.  **Edge Device (Raspberry Pi)**:
    *   **Audio Monitor** (`src/device/audio_monitor.py`): Runs a local PyTorch model to detect baby cries in real-time. Logs events to BigQuery and uploads audio clips to GCS.
    *   **Video Server** (`src/device/camera_server.py`): Streams low-latency MJPEG video from the Pi Camera.
    *   **Environment Monitor** (`src/device/environment_monitor.py`): Logs temperature, humidity, and pressure using a BME280 sensor to BigQuery.
    *   **Service Runner** (`src/device/start_services.py`): Orchestrates all device services concurrently using multiprocesing.

2.  **Backend API (FastAPI)**:
    *   Proxies the video feed for secure remote access.
    *   Provides REST endpoints for manual event logging (Feeding, Sleep, Diaper).
    *   Retrieves historical logs and analytics from BigQuery.

3.  **Frontend (React + Tailwind)**:
    *   **Monitor**: Real-time video feed and status cards.
    *   **Logging**: fast interface for tracking daily care events.
    *   **Analytics**: Interactive charts for sleep patterns, feeding volumes, cry frequency, and environmental trends.

4.  **AI Agent**:
    *   An autonomous agent (`baby_monitor_agent`) capable of interacting with the system's data and logs.

## Hardware Requirements

*   Raspberry Pi 4 (or similar)
*   USB Microphone
*   Raspberry Pi Camera Module
*   BME280 Sensor (I2C)

## Quick Start

### 1. Web Application (Mac/PC)

The backend and frontend are Dockerized for easy deployment.

```bash
# Create a .env file with your credentials (see .env.example)
# Then run:
docker compose up --build
```

Access the app at: `http://localhost:8000` (Frontend is served by the backend or separate dev server depending on config).

### 2. Device Services (Raspberry Pi)

SSH into your Raspberry Pi and run the all-in-one service runner:

```bash
# Ensure you are in the project root
python3 src/device/start_services.py
```

This will launch:
*   Microphone listening & inference
*   Camera streaming (Port 8080)
*   Environment sensor logging

### 3. AI Agent

To run the autonomous agent:

```bash
adk run baby_monitor_agent
```

## Configuration

Required environment variables (`.env`):

```env
# Cloud Config
GCP_PROJECT_ID=your-project-id
BIGQUERY_TABLE_ID=your-project.dataset.table
BIGQUERY_LOGS_TABLE_ID=your-project.dataset.logs
BIGQUERY_TABLE_ID_ENV=your-project.dataset.environment
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Device Config
CAMERA_SERVER_URL=http://<PI_IP>:8080/video_feed
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/... (Optional)
```

## Directory Structure

*   `src/api`: FastAPI backend.
*   `src/device`: Python scripts running on the edge hardware.
*   `src/model`: PyTorch model training and definition.
*   `frontend`: React application.
*   `baby_monitor_agent`: GenAI agent implementation.
