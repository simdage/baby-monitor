import streamlit as st
import pandas as pd
import time
import sys
from pathlib import Path

import base64
import io
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from google.cloud import storage

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

import src.detection_service.db as db

st.set_page_config(
    page_title="Baby Monitor Dashboard",
    page_icon="👶",
    layout="wide"
)

st.title("👶 Baby Monitor Dashboard")

# Auto-refresh
if st.checkbox("Auto-refresh", value=True):
    time.sleep(2)
    st.rerun()

# Fetch data
# Switch to BigQuery
data = db.get_recent_predictions_bigquery(limit=500)

print("Data:", data)
# data = db.get_recent_predictions(limit=500) # Fallback to SQLite

if not data:
    st.warning("No data available yet. Start the prediction service!")
else:
    df = pd.DataFrame(data, columns=["timestamp", "probability", "is_cry", "audio_gcs_uri"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
    df = df.sort_values("timestamp")

    # Metrics
    latest = df.iloc[-1]
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Probability", f"{latest['probability']:.2f}")
    
    with col2:
        status = "👶 CRYING!" if latest['is_cry'] else "😴 Sleeping"
        color = "inverse" if latest['is_cry'] else "normal"
        st.metric("Status", status)
        
    with col3:
        last_cry = df[df["is_cry"] == True]["datetime"].max()
        if pd.isna(last_cry):
            st.metric("Last Cry", "Never")
        else:
            st.metric("Last Cry", last_cry.strftime("%H:%M:%S"))

    # Chart
    st.subheader("Cry Probability (Last 500 readings)")
    st.line_chart(df.set_index("datetime")["probability"])

    # Recent Alerts
    st.subheader("Recent Alerts")
    alerts = df[df["is_cry"] == True].sort_values("timestamp", ascending=False).head(10)
    if not alerts.empty:
        st.dataframe(
            alerts[["datetime", "probability"]].style.format({"probability": "{:.2f}"}),
            use_container_width=True
        )
    else:
        st.info("No recent alerts.")

    # Audio Analysis
    st.subheader("Audio Analysis")
    
    # Create a label with timestamp and probability
    df['label'] = df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S') + " (Prob: " + df['probability'].apply(lambda x: f"{x:.2f}") + ")"
    
    # Default to the most recent record
    selected_label = st.selectbox("Select Record", df['label'].tolist(), index=len(df)-1) # default to last
    
    # Get the selected row
    selected_row = df[df['label'] == selected_label].iloc[0]
    
    if selected_row['audio_gcs_uri']:
        try:
            # Handle potential None if column is null
            if pd.isna(selected_row['audio_gcs_uri']):
                 st.info("No audio data available for this record.")
            else:
                # Download from GCS
                gcs_uri = selected_row['audio_gcs_uri']
                
                # Simple parsing of gs://bucket/path
                if gcs_uri.startswith("gs://"):
                    parts = gcs_uri.replace("gs://", "").split("/", 1)
                    bucket_name = parts[0]
                    blob_name = parts[1]
                    
                    storage_client = storage.Client()
                    bucket = storage_client.bucket(bucket_name)
                    blob = bucket.blob(blob_name)
                    
                    audio_bytes = blob.download_as_bytes()
                else:
                    st.error(f"Invalid GCS URI: {gcs_uri}")
                    audio_bytes = None

                if audio_bytes:
                    # Play Audio
                    st.audio(audio_bytes, format='audio/wav')
                    
                    # Spectrogram
                    try:
                        # BytesIO to read as file
                        wav_file = io.BytesIO(audio_bytes)
                        rate, data = wavfile.read(wav_file)
                        
                        # If stereo, take one channel
                        if len(data.shape) > 1:
                            data = data[:, 0]
                            
                        fig, ax = plt.subplots(figsize=(10, 4))
                        Pxx, freqs, bins, im = ax.specgram(data, Fs=rate)
                        ax.set_title("Spectrogram")
                        ax.set_ylabel("Frequency")
                        ax.set_xlabel("Time")
                        st.pyplot(fig)
                        plt.close(fig) 
                        
                    except Exception as e:
                        # Fallback for raw PCM (legacy/broken files)
                        try:
                            # Assuming 16kHz float32 mono based on prediction service
                            data = np.frombuffer(audio_bytes, dtype=np.float32)
                            rate = 16000
                            
                            fig, ax = plt.subplots(figsize=(10, 4))
                            Pxx, freqs, bins, im = ax.specgram(data, Fs=rate)
                            ax.set_title("Spectrogram (Raw PCM fallback)")
                            ax.set_ylabel("Frequency")
                            ax.set_xlabel("Time")
                            st.pyplot(fig)
                            plt.close(fig)
                            st.warning("Visualization generated from raw PCM data (missing WAV header). Audio player might not work.")
                        except Exception as fallback_error:
                            st.error(f"Error generating spectrogram: {e}")
                
        except Exception as e:
            st.error(f"Error loading audio from GCS: {e}")
    else:
        st.info("No audio data available for this record.")
