from apache_beam.options.pipeline_options import PipelineOptions


class DataflowStarterKitOptions(PipelineOptions):
    """Custom pipeline options"""

    @classmethod
    def _add_argparse_args(cls, parser):
        """Add custom command-line arguments."""
        parser.add_argument(
            '--input',
            default='1',
            help='Input multiplier (number of times to repeat input data)')
