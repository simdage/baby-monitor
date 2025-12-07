import argparse
import json
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions

class ParseJson(beam.DoFn):
    """Parses the raw JSON string."""
    def process(self, element):
        try:
            record = json.loads(element)
            yield record
        except Exception as e:
            logging.error(f"Error parsing JSON: {e}")

class FormatForBigQuery(beam.DoFn):
    """Formats the dictionary for BigQuery."""
    def process(self, element):
        try:
            # Ensure fields match BigQuery schema
            output = {
                'timestamp': element.get('timestamp'),
                'probability': element.get('probability'),
                'is_cry': element.get('is_cry'),
                'audio_data': element.get('audio_data') # Optional, might be None
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
    
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session

    # BigQuery Schema
    table_schema = {
        'fields': [
            {'name': 'timestamp', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
            {'name': 'probability', 'type': 'FLOAT', 'mode': 'REQUIRED'},
            {'name': 'is_cry', 'type': 'BOOLEAN', 'mode': 'REQUIRED'},
            {'name': 'audio_data', 'type': 'STRING', 'mode': 'NULLABLE'},
        ]
    }

    with beam.Pipeline(options=pipeline_options) as p:
        (
            p
            | 'ReadFromGCS' >> beam.io.ReadFromText(known_args.input_bucket)
            | 'ParseJSON' >> beam.ParDo(ParseJson())
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
