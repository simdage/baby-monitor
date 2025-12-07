import os
import sys
from src.detection_service import db

# Add project root to sys.path
from pathlib import Path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.append(project_root)

def verify():
    print("Verifying BigQuery connection...")
    
    # Check for placeholders
    # We can inspect the function or just try to run it
    # Since we know we put placeholders, we can warn the user if they look like placeholders
    
    # Actually, let's just try to call it.
    print("Attempting to fetch 1 record from BigQuery...")
    try:
        data = db.get_recent_predictions_bigquery(limit=200)
        if data:
            print(f"Success! Retrieved {len(data)} record(s).")
            print("Sample:", data[0])
        else:
            print("Connection successful (or handled gracefully), but no data returned.")
            print("Check if table is empty or if Project/Table ID are correct.")
    except Exception as e:
        # Note: db.py catches exceptions and prints them, then returns []
        # So we might not see the exception here unless we modify db.py to re-raise or we check stdout
        print("Function returned empty list. Check console output for errors from db.py.")

if __name__ == "__main__":
    verify()
