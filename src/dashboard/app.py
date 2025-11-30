import streamlit as st
import pandas as pd
import time
import sys
from pathlib import Path

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
data = db.get_recent_predictions(limit=500)

if not data:
    st.warning("No data available yet. Start the prediction service!")
else:
    df = pd.DataFrame(data, columns=["timestamp", "probability", "is_cry"])
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
