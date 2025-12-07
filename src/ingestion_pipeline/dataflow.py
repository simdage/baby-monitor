import argparse
import json
import logging
import base64
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
    def __init__(self, output_bucket):
        self.output_bucket = output_bucket

    def process(self, element):
        try:
            audio_data = element.get('audio_data')
            timestamp = element.get('timestamp')
            
            if audio_data and timestamp:
                # Decode base64
                audio_bytes = base64.b64decode(audio_data)
                
                # Create GCS path
                # Ideally, we should use a proper filename structure
                filename = f"audio/{timestamp}.wav"
                gcs_uri = f"gs://{self.output_bucket}/{filename}"
                
                # Write to GCS
                storage_client = storage.Client()
                bucket = storage_client.bucket(self.output_bucket)
                blob = bucket.blob(filename)
                
                # Upload bytes. Assuming audio_data is already a valid WAV file encoded in base64.
                # If it's raw PCM, we would need to wrap it with RIFF header using wave module.
                # Based on previous context, we treated it as WAV.
                blob.upload_from_string(audio_bytes, content_type='audio/wav')
                
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
