import sqlite3
import time
from pathlib import Path

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
