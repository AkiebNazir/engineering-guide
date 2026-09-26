import argparse
import json
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms.window import SlidingWindows
from apache_beam.transforms.trigger import AfterWatermark, AfterProcessingTime, AccumulationMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParseEvent(beam.DoFn):
    def process(self, element):
        try:
            # Assuming incoming element is a JSON string from Kafka or PubSub
            event = json.loads(element.decode('utf-8'))
            # We must yield a timestamped element for windowing to work
            # For simplicity, returning a tuple (key, value)
            yield (event.get("category", "unknown"), event.get("value", 0.0))
        except Exception as e:
            logger.error(f"Failed to parse event: {e}")

def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_topic', default='projects/my-project/topics/input-topic')
    parser.add_argument('--output_topic', default='projects/my-project/topics/output-topic')
    known_args, pipeline_args = parser.parse_known_args(argv)

    # Set up PipelineOptions for streaming
    pipeline_options = PipelineOptions(
        pipeline_args,
        streaming=True,
        save_main_session=True
    )

    logger.info("Starting Sliding Window Aggregator pipeline...")

    with beam.Pipeline(options=pipeline_options) as p:
        # Read from PubSub (as a stand-in for streaming source)
        events = (
            p 
            | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(topic=known_args.input_topic)
            | 'ParseEvent' >> beam.ParDo(ParseEvent())
        )

        # Apply sliding window: 5-minute window, sliding every 1 minute
        windowed_events = (
            events
            | 'ApplySlidingWindow' >> beam.WindowInto(
                SlidingWindows(size=300, period=60),
                trigger=AfterWatermark(early=AfterProcessingTime(10)),
                accumulation_mode=AccumulationMode.DISCARDING
            )
        )

        # Aggregate data: Sum values per category within the window
        aggregated = (
            windowed_events
            | 'SumPerCategory' >> beam.CombinePerKey(sum)
            | 'FormatOutput' >> beam.Map(lambda kv: json.dumps({"category": kv[0], "sum": kv[1]}).encode('utf-8'))
        )

        # Write aggregated results to PubSub
        aggregated | 'WriteToPubSub' >> beam.io.WriteToPubSub(topic=known_args.output_topic)

if __name__ == '__main__':
    run()
