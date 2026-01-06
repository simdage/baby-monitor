import base64
import json
import os
from google.cloud import bigquery
from datetime import datetime

# Initialize the BigQuery Client once (global scope) for performance
bq_client = bigquery.Client()

BIG_QUERY_TABLE_ID = os.environ.get('BIG_QUERY_TABLE_ID')

def ingest_cry_event(event, context):
    """
    Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    try:
        # 1. Decode the Pub/Sub message
        if 'data' in event:
            pubsub_message = base64.b64decode(event['data']).decode('utf-8')
            message_json = json.loads(pubsub_message)
        else:
            print("Error: No data in Pub/Sub message")
            return "No Data", 400

        print(f"Processing event: {message_json.get('event_id', 'unknown')}")

        # 2. Prepare the row for BigQuery
        # Note: 'timestamp' from Pi comes as float (Unix epoch). 
        # BQ expects a datetime object or specific string format.
        timestamp_float = message_json.get('timestamp')
        timestamp_dt = datetime.fromtimestamp(timestamp_float).isoformat() if timestamp_float else None

        row_to_insert = {
            "event_id": message_json.get('event_id'),
            "event_timestamp": timestamp_dt,
            "device_id": message_json.get('device_id', 'pi-nursery-01'), # Add this to your Pi code later
            "probability": message_json.get('probability'),
            "is_cry": message_json.get('is_cry'),
            "gcs_uri": message_json.get('gcs_uri'),
        }

        # 3. Insert into BigQuery
        table_ref = f"{bq_client.project}.{BIG_QUERY_TABLE_ID}"
        
        errors = bq_client.insert_rows_json(table_ref, [row_to_insert])

        if errors:
            print(f"Encountered errors while inserting rows: {errors}")
            # Raising an exception forces Pub/Sub to retry the message
            raise RuntimeError("BigQuery insertion failed")
            
        print("Successfully inserted row into BigQuery")
        return "Success", 200

    except Exception as e:
        print(f"Critical Error: {e}")
        # Re-raising the exception marks the function as 'Failed'
        # Pub/Sub will retry based on your retry policy.
        raise e