import os
import json
import base64
import time
import threading
import queue
from google.cloud import pubsub_v1, storage
from google.api_core import exceptions
from dotenv import load_dotenv
import uuid
import io
import scipy.io.wavfile

load_dotenv()

class Publisher:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.topic_id = os.getenv("GCP_TOPIC_ID")
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        
        self.publisher = None
        self.topic_path = None
        self.storage_client = None
        self.bucket = None
        
        self.queue = queue.Queue()
        self.running = False
        self.thread = None
        
        if self.project_id and self.topic_id:
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(self.project_id, self.topic_id)
            self.start()
            print(f"✅ Pub/Sub initialized: {self.topic_path}")

        else:
            raise ValueError("GCP_PROJECT_ID or GCP_TOPIC_ID not set. Pub/Sub disabled.")
            
        if self.bucket_name:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.bucket_name)
            print(f"✅ GCS Storage initialized: gs://{self.bucket_name}")
            if not self.running: # Start thread if not already started by Pub/Sub
                self.start()
        else:
            raise ValueError("GCS_BUCKET_NAME not set. GCS disabled.")

    def start(self):
        """Start the background worker thread."""
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the background worker thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def publish(self, probability, is_cry, audio_buffer=None, sample_rate=16000):
        """Enqueue a message for publishing."""
        if not self.publisher:
            return

        # usage of uuid ensures no filename collisions if clocks sync weirdly
        event_id = str(uuid.uuid4())
        
        message = {
            "event_id": event_id,
            "timestamp": time.time(),
            "probability": float(probability),
            "is_cry": bool(is_cry),
            "sample_rate": sample_rate
        }
        
        # Only attach audio data if it exists
        if audio_buffer is not None:
            message["audio_buffer"] = audio_buffer # Pass raw numpy array to thread
            
        self.queue.put(message)

    def _worker(self):
        """Background worker to publish messages."""
        while self.running:
            try:
                # Get message
                task = self.queue.get(timeout=1.0)
                
                gcs_uri = None

                # 1. Handle GCS Upload (Write WAV, not JSON)
                if self.bucket and "audio_buffer" in task:
                    try:
                        # Create a WAV file in memory
                        byte_io = io.BytesIO()
                        # Convert float32 0-1 range to Int16 usually better for standard WAV compatibility
                        # But float32 works in modern players too.
                        scipy.io.wavfile.write(byte_io, task['sample_rate'], task['audio_buffer'])
                        byte_io.seek(0)
                        
                        # Define path: year/month/day helps with organizing millions of files
                        blob_name = f"raw/{task['event_id']}.wav"
                        blob = self.bucket.blob(blob_name)
                        
                        blob.upload_from_file(byte_io, content_type='audio/wav')
                        gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
                        # print(f"Uploaded: {gcs_uri}")
                    except Exception as e:
                        print(f"GCS Upload Error: {e}")

                # 2. Prepare Pub/Sub Payload (The Claim Check)
                pubsub_payload = {
                    "event_id": task["event_id"],
                    "timestamp": task["timestamp"],
                    "probability": task["probability"],
                    "is_cry": task["is_cry"],
                    "gcs_uri": gcs_uri 
                }
                
                # 3. Publish
                if self.publisher and self.topic_path:
                    data_bytes = json.dumps(pubsub_payload).encode("utf-8")
                    future = self.publisher.publish(self.topic_path, data_bytes)
                    future.result() 
                
                self.queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
