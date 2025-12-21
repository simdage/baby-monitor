import sqlite3
import time
import os
from pathlib import Path
from google.cloud import bigquery
from dotenv import load_dotenv
load_dotenv()

# Database path
DB_PATH = Path(__file__).resolve().parents[2] / "predictions.db"

def init_db():
    """Initialize the database table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            probability REAL,
            is_cry BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

def log_prediction(probability, is_cry):
    """Log a prediction to the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO predictions (timestamp, probability, is_cry) VALUES (?, ?, ?)",
        (time.time(), probability, is_cry)
    )
    conn.commit()
    conn.close()

def get_recent_predictions(limit=1000):
    """Get recent predictions."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT timestamp, probability, is_cry FROM predictions ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    data = c.fetchall()
    conn.close()
    return data

def get_recent_predictions_bigquery(limit=500):
    """Get recent predictions from BigQuery."""
    # TODO: Replace with your actual Project ID and Table ID
    project_id = os.getenv("GCP_PROJECT_ID") 
    table_id = os.getenv("BIGQUERY_TABLE_ID")
    
    client = bigquery.Client(project=project_id)
    
    query = f"""
        SELECT event_timestamp, probability, is_cry, gcs_uri
        FROM `{project_id}.{table_id}`
        ORDER BY event_timestamp DESC
        LIMIT {limit}
    """
    
    try:
        query_job = client.query(query)
        results = query_job.result()
        
        # Convert to list of dicts or tuples to match existing format
        # existing format seems to be list of tuples: (timestamp, probability, is_cry)
        data = []
        for row in results:
            data.append((row.event_timestamp.timestamp(), row.probability, row.is_cry, row.gcs_uri))
            
        return data
    except Exception as e:
        print(f"Error querying BigQuery: {e}")
        return []
