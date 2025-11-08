"""Transform operations for data processing."""

import logging

import apache_beam as beam


class ProcessElement(beam.DoFn):
    """Simple transform to process each element."""

    def process(self, element: str):
        """
        Process a single element.

        Args:
            element: Input string element (format: "Name - time")

        Yields:
            Processed float element (lap time)
        """
        try:
            # Extract time from "Name - time" format
            time_str = element.split('-')[1].strip()
            processed = float(time_str)
            logging.info(f"Element - {element} -> {processed}")
            yield processed
        except Exception as e:
            logging.error(f"Error processing element '{element}': {str(e)}")
