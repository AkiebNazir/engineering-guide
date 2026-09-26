import uuid
import datetime
from openlineage.client import OpenLineageClient, set_producer
from openlineage.client.run import RunEvent, RunState, Run, Job
from openlineage.client.transport.console import ConsoleTransport
from openlineage.client.facet import (
    DocumentationJobFacet, 
    SchemaDatasetFacet, 
    SchemaField, 
    SourceCodeJobFacet
)
from openlineage.client.dataset import Dataset

def main():
    # Set the producer URL indicating the application emitting the events
    set_producer("https://github.com/OpenLineage/OpenLineage/tree/main/integration/python")
    
    # Use a ConsoleTransport to output OpenLineage events to stdout (useful for local testing/demo)
    # In production, use HttpTransport pointing to Marquez or another OpenLineage backend
    client = OpenLineageClient(transport=ConsoleTransport())

    # Define the inputs and outputs for this job run
    input_dataset = Dataset(
        namespace="postgres://oltp-db-prod:5432",
        name="public.raw_transactions",
        facets={
            "schema": SchemaDatasetFacet(
                fields=[
                    SchemaField(name="txn_id", type="INT"),
                    SchemaField(name="amount", type="DECIMAL"),
                    SchemaField(name="user_id", type="INT")
                ]
            )
        }
    )

    output_dataset = Dataset(
        namespace="snowflake://warehouse-prod",
        name="sales_mart.fct_daily_sales",
        facets={
            "schema": SchemaDatasetFacet(
                fields=[
                    SchemaField(name="date", type="DATE"),
                    SchemaField(name="total_amount", type="DECIMAL")
                ]
            )
        }
    )

    job = Job(
        namespace="airflow_production",
        name="daily_sales_aggregation",
        facets={
            "documentation": DocumentationJobFacet(
                description="Aggregates raw transactions into daily sales facts."
            ),
            "sourceCode": SourceCodeJobFacet(
                language="python",
                sourceCode="SELECT date, SUM(amount) FROM raw_transactions GROUP BY date"
            )
        }
    )

    run_id = str(uuid.uuid4())
    run = Run(runId=run_id)

    # Emit a START event
    print("Emitting OpenLineage START event...")
    start_event = RunEvent(
        eventType=RunState.START,
        eventTime=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        run=run,
        job=job,
        inputs=[input_dataset],
        producer="https://github.com/OpenLineage/OpenLineage/tree/main/integration/python"
    )
    client.emit(start_event)

    # Simulate job execution
    print("\nRunning ETL job...")
    
    # Emit a COMPLETE event
    print("\nEmitting OpenLineage COMPLETE event...")
    complete_event = RunEvent(
        eventType=RunState.COMPLETE,
        eventTime=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        run=run,
        job=job,
        outputs=[output_dataset],
        producer="https://github.com/OpenLineage/OpenLineage/tree/main/integration/python"
    )
    client.emit(complete_event)
    print("\nOpenLineage events successfully emitted (printed to console).")

if __name__ == "__main__":
    main()
