"""Main pipeline entry point."""

import logging

import apache_beam as beam

from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

from dataflow_starter_kit.options.starter_kit_options import DataflowStarterKitOptions
from dataflow_starter_kit.transforms.transform import ProcessElement
from dataflow_starter_kit.utils import config


def run():
    """Main pipeline function."""
    pipeline_options = PipelineOptions()
    pipeline_options.view_as(SetupOptions).save_main_session = True
    pipeline_arguments = pipeline_options.view_as(DataflowStarterKitOptions)

    input_count = int(pipeline_arguments.input)

    logging.info(f"Starting pipeline with input_count={input_count}")
    
    with beam.Pipeline(options=pipeline_options) as p:
        # Create input data (repeat based on input argument)
        input_data = config.INPUT_DATA * input_count
        lines = p | 'CreateInput' >> beam.Create(input_data)
        
        # Apply transform
        transformed = lines | 'ProcessElement' >> beam.ParDo(ProcessElement())
        
        # Aggregate results
        total = transformed | 'SumAll' >> beam.CombineGlobally(sum)
        
        # Log/print results
        _ = total | 'PrintResults' >> beam.Map(lambda x: logging.info(f"Total time: {x:.3f}s"))
    
    logging.info("Pipeline completed successfully")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run()