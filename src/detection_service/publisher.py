import os
import json
import base64
import time
import threading
import queue
from google.cloud import pubsub_v1
from google.api_core import exceptions

class Publisher:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.topic_id = os.getenv("GCP_TOPIC_ID")
        self.publisher = None
        self.topic_path = None
        self.queue = queue.Queue()
        self.running = False
        self.thread = None
        
        if self.project_id and self.topic_id:
            try:
                self.publisher = pubsub_v1.PublisherClient()
                self.topic_path = self.publisher.topic_path(self.project_id, self.topic_id)
                self.start()
                print(f"✅ Pub/Sub initialized: {self.topic_path}")
            except Exception as e:
                print(f"⚠️  Pub/Sub initialization failed: {e}")
        else:
            print("⚠️  GCP_PROJECT_ID or GCP_TOPIC_ID not set. Pub/Sub disabled.")

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

    def publish(self, probability, is_cry, audio_buffer=None):
        """Enqueue a message for publishing."""
        if not self.publisher:
            return

        message = {
            "timestamp": time.time(),
            "probability": float(probability),
            "is_cry": bool(is_cry)
        }
        
        if audio_buffer is not None:
            # Convert numpy array to bytes, then base64 string
            audio_bytes = audio_buffer.tobytes()
            message["audio_data"] = base64.b64encode(audio_bytes).decode('utf-8')
            
        self.queue.put(message)

    def _worker(self):
        """Background worker to publish messages."""
        while self.running:
            try:
                # Get message with timeout to allow checking self.running
                message = self.queue.get(timeout=1.0)
                
                data_str = json.dumps(message)
                data = data_str.encode("utf-8")
                
                try:
                    future = self.publisher.publish(self.topic_path, data)
                    future.result()  # Wait for confirmation
                    # print(f"Published message to {self.topic_id}")
                except Exception as e:
                    print(f"Failed to publish message: {e}")
                    
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
