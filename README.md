# Baby Cry Monitoring System

A comprehensive system to detect infant crying using machine learning, process audio data in the cloud, and visualize results on a real-time dashboard.

## Architecture

1.  **Edge Detection**: Captures audio and runs inference locally.
2.  **Data Ingestion**: Uploads raw data to Google Cloud Storage (GCS).
3.  **Processing Pipeline**: Apache Beam/Dataflow pipeline that:
    *   Reads raw JSON data from GCS.
    *   Decodes base64 audio and saves as WAV files to a "processed audio" GCS bucket.
    *   Writes metadata (timestamp, probability, is_cry, audio_uri) to BigQuery.
4.  **Dashboard**: Streamlit app that queries BigQuery for insights and fetches audio files from GCS for playback and spectrogram visualization.

## Prerequisites

- Python 3.8+
- Google Cloud Platform account with:
    - BigQuery enabled
    - Cloud Storage enabled
    - Dataflow enabled
- Service account credentials (`google_application_credentials.json`)

## Configuration

Create a `.env` file in the root directory:

```env
GCP_PROJECT_ID=your-project-id
BIGQUERY_TABLE_ID=your-project-id.dataset.table
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

## Installation

```bash
# Install dependencies using uv (or pip)
uv sync
# OR
pip install -r requirements.txt
```

## Components

### 1. Dashboard

The dashboard allows you to monitor cry events, view probabilities over time, and listen to recorded audio.

**Run the dashboard:**
```bash
streamlit run src/dashboard/app.py
```

### 2. Ingestion Pipeline

The Dataflow pipeline processes data from the edge device.

**Run locally/Dataflow:**
```bash
python src/ingestion_pipeline/dataflow.py \
  --input_bucket "gs://audio_logs/raw/*" \
  --output_table "baby-monitor-479819:baby_analytics.prediction_service" \
  --audio_output_bucket "gs://audio_logs/audio/*" \
  --runner DirectRunner \
  --project baby-monitor-479819 \
  --temp_location "gs://audio_logs/temp/"
```

### 3. Database Migration

If you need to update the schema (e.g., when moving from specific audio data to GCS URIs):
Check `schema_migration.sql` for SQL commands to alter the BigQuery table.

## Development

- **`src/detection_service`**: Contains database interaction logic (`db.py`) and specific audio processing logic for the edge.
- **`src/dashboard`**: UI logic.
- **`src/ingestion_pipeline`**: Cloud processing logic.
