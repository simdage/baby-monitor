import logging
import unittest
import json
import os
import shutil
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that
from apache_beam.testing.util import equal_to
import apache_beam as beam
from src.ingestion_pipeline.dataflow import ParseJson, FormatForBigQuery

class TestDataflowPipeline(unittest.TestCase):

    def test_parse_json(self):
        with TestPipeline() as p:
            input_data = ['{"a": 1, "b": 2}']
            output = (
                p
                | beam.Create(input_data)
                | beam.ParDo(ParseJson())
            )
            print("Output:", output)
            assert_that(output, equal_to([{'a': 1, 'b': 2}]))

    def test_format_for_bigquery(self):
        with TestPipeline() as p:
            input_data = [{'timestamp': 1.0, 'probability': 0.9, 'is_cry': True, 'audio_data': 'abc', 'extra': 'ignore'}]
            expected_output = [{'timestamp': 1.0, 'probability': 0.9, 'is_cry': True, 'audio_data': 'abc'}]
            
            output = (
                p
                | beam.Create(input_data)
                | beam.ParDo(FormatForBigQuery())
            )
            print("Output:", output)
            print("Expected output:", expected_output)
            assert_that(output, equal_to(expected_output))

if __name__ == '__main__':
    #logging.getLogger().setLevel(logging.INFO)
    unittest.main()
