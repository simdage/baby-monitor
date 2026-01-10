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
    
    client = bigquery.Client(project=project_id, location="northamerica-northeast1")
    
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

def log_manual_event_bigquery(event_type, notes, timestamp_iso, intensity, milk_quantity_ml=None, feeding_time_min=None):
    """Log a manual event to BigQuery."""
    project_id = os.getenv("GCP_PROJECT_ID")
    # Default to daily_logs if not specified
    table_id = os.getenv("BIGQUERY_LOGS_TABLE_ID", "baby_analytics.daily_logs")
    
    client = bigquery.Client(project=project_id, location="northamerica-northeast1")
    
    # Table schema expected: event_type (STRING), notes (STRING), event_timestamp (TIMESTAMP), intensity (STRING), milk_quantity_ml (INTEGER/FLOAT), feeding_time_min (INTEGER/FLOAT)
    # Ensure correct format for BQ
    row_to_insert = {
        "event_type": event_type,
        "notes": notes,
        "event_timestamp": timestamp_iso, # Expecting ISO string or datetime
        "intensity": intensity,
        "milk_quantity_ml": milk_quantity_ml,
        "feeding_time_min": feeding_time_min
    }
    
    try:
        table_ref = f"{project_id}.{table_id}"
        errors = client.insert_rows_json(table_ref, [row_to_insert])
        
        if errors:
            print(f"BigQuery Errors: {errors}")
            return False
        return True
    except Exception as e:
        print(f"Error inserting into BigQuery: {e}")
        return False

def get_manual_logs_bigquery(limit=100):
    """Fetch recent manual logs from BigQuery."""
    project_id = os.getenv("GCP_PROJECT_ID")
    table_id = os.getenv("BIGQUERY_LOGS_TABLE_ID", "baby_analytics.daily_logs")
    
    client = bigquery.Client(project=project_id, location="northamerica-northeast1")
    
    # Select new columns if they exist. Using * might be safer if schema changes often, 
    # but explicit selection is better for code clarity. 
    # Let's try to select them, assuming the user has indeed added them to the schema.
    query = f"""
        SELECT event_type, notes, event_timestamp, intensity, milk_quantity_ml, feeding_time_min
        FROM `{project_id}.{table_id}`
        ORDER BY event_timestamp DESC
        LIMIT {limit}
    """
    
    try:
        query_job = client.query(query)
        results = query_job.result()
        
        data = []
        for row in results:
            # Return dicts directly
            data.append({
                "type": row.event_type,
                "details": row.notes,
                "timestamp": row.event_timestamp.isoformat(), # Return ISO string for consistency
                "time_display": row.event_timestamp.strftime("%I:%M %p"), # Pre-format time string
                "intensity": row.intensity,
                "milk_quantity_ml": row.milk_quantity_ml,
                "feeding_time_min": row.feeding_time_min
            })
            
        return data
    except Exception as e:
        print(f"Error querying BigQuery Logs: {e}")
        return []
