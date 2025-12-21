import argparse
import json
import logging
import base64
import io
import numpy as np
from scipy.io import wavfile
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from google.cloud import storage

class ParseJson(beam.DoFn):
    """Parses the raw JSON string."""
    def process(self, element):
        try:
            record = json.loads(element)
            yield record
        except Exception as e:
            logging.error(f"Error parsing JSON: {e}")

class WriteAudioToGCS(beam.DoFn):
    """Writes audio data to GCS as WAV and updates the record."""
    def __init__(self, output_path):
        self.output_path = output_path.rstrip('/')
        # Parse bucket and prefix
        # Expected format: gs://bucket/prefix/ or just bucket
        if self.output_path.startswith("gs://"):
            parts = self.output_path.replace("gs://", "").split("/", 1)
            self.bucket_name = parts[0]
            self.prefix = parts[1] if len(parts) > 1 else ""
        else:
            self.bucket_name = self.output_path
            self.prefix = "audio" # Default prefix if only bucket name provided

    def process(self, element):
        try:
            audio_data = element.get('audio_data')
            timestamp = element.get('timestamp')
            
            if audio_data and timestamp:
                # Decode base64
                audio_bytes = base64.b64decode(audio_data)
                
                # Create GCS path
                if self.prefix:
                    # If prefix contains wildcards (e.g. audio/*), strip them
                    clean_prefix = self.prefix.rstrip('*').rstrip('/')
                    filename = f"{clean_prefix}/{timestamp}.wav"
                else:
                    filename = f"audio/{timestamp}.wav" # Should not happen with parsing above but safeguard
                
                gcs_uri = f"gs://{self.bucket_name}/{filename}"
                
                # Write to GCS
                storage_client = storage.Client()
                bucket = storage_client.bucket(self.bucket_name)
                blob = bucket.blob(filename)
                
                # Convert raw PCM bytes to numpy array
                # Prediction service sends float32 (tobytes)
                audio_np = np.frombuffer(audio_bytes, dtype=np.float32)

                # Write WAV file to memory buffer
                with io.BytesIO() as wav_buffer:
                    # SAMPLE_RATE is known to be 16000 from prediction.py
                    wavfile.write(wav_buffer, 16000, audio_np)
                    wav_content = wav_buffer.getvalue()

                    # Upload WAV content
                    blob.upload_from_string(wav_content, content_type='audio/wav')
                
                # Update element
                element['audio_gcs_uri'] = gcs_uri
                del element['audio_data']
            else:
                element['audio_gcs_uri'] = None
                
            yield element
        except Exception as e:
            logging.error(f"Error writing audio to GCS: {e}")
            # Yield element without audio info if failure, or handle otherwise?
            # For now, let's yield with None uri so we still get the prediction
            element['audio_gcs_uri'] = None
            if 'audio_data' in element:
                del element['audio_data']
            yield element

class FormatForBigQuery(beam.DoFn):
    """Formats the dictionary for BigQuery."""
    def process(self, element):
        try:
            # Ensure fields match BigQuery schema
            output = {
                'timestamp': element.get('timestamp'),
                'probability': element.get('probability'),
                'is_cry': element.get('is_cry'),
                'audio_gcs_uri': element.get('audio_gcs_uri')
            }
            yield output
        except Exception as e:
            logging.error(f"Error formatting for BigQuery: {e}")

def run(argv=None, save_main_session=True):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_bucket',
        dest='input_bucket',
        required=True,
        help='Input GCS bucket or pattern to read from.')
    parser.add_argument(
        '--output_table',
        dest='output_table',
        required=True,
        help='BigQuery table to write to.')
    parser.add_argument(
        '--audio_output_bucket',
        dest='audio_output_bucket',
        required=True,
        help='GCS bucket to write audio files to.')
    
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session

    # BigQuery Schema
    table_schema = {
        'fields': [
            {'name': 'timestamp', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
            {'name': 'probability', 'type': 'FLOAT', 'mode': 'REQUIRED'},
            {'name': 'is_cry', 'type': 'BOOLEAN', 'mode': 'REQUIRED'},
            {'name': 'audio_gcs_uri', 'type': 'STRING', 'mode': 'NULLABLE'},
        ]
    }

    with beam.Pipeline(options=pipeline_options) as p:
        (
            p
            | 'ReadFromGCS' >> beam.io.ReadFromText(known_args.input_bucket)
            | 'ParseJSON' >> beam.ParDo(ParseJson())
            | 'WriteAudioToGCS' >> beam.ParDo(WriteAudioToGCS(known_args.audio_output_bucket))
            | 'FormatForBigQuery' >> beam.ParDo(FormatForBigQuery())
            | 'WriteToBigQuery' >> beam.io.WriteToBigQuery(
                known_args.output_table,
                schema=table_schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
            )
        )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
