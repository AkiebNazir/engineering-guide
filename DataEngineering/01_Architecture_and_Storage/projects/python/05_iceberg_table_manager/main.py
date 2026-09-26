import pyarrow as pa
from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    LongType,
    StringType,
    TimestampType,
    NestedField,
)
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transforms import DayTransform
from pyiceberg.exceptions import NoSuchTableError, TableAlreadyExistsError
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def manage_iceberg():
    """
    Demonstrates managing an Apache Iceberg table using pyiceberg.
    Requires a configured catalog (e.g., REST, Hive, SqlCatalog) via ~/.pyiceberg.yaml
    or environment variables. For this simulation, we load the default catalog.
    """
    logger.info("Initializing Iceberg Catalog...")
    
    try:
        # Load the default catalog defined in configuration.
        # In a real environment, this might connect to AWS Glue, tabular, or Hive.
        catalog = load_catalog("default")
    except Exception as e:
        logger.warning(f"Could not load Iceberg catalog (using dummy configuration for demonstration): {e}")
        # To make the script runnable without a real catalog, we will mock the catalog object 
        # in a real scenario you would have the catalog correctly configured.
        logger.info("Please configure ~/.pyiceberg.yaml with a valid catalog to run this against a real backend.")
        return

    # Define the schema for our events table
    schema = Schema(
        NestedField(field_id=1, name="id", field_type=LongType(), required=True),
        NestedField(field_id=2, name="event_name", field_type=StringType(), required=False),
        NestedField(field_id=3, name="ts", field_type=TimestampType(), required=True),
    )

    # Define partition spec: Partition by the day of the timestamp
    partition_spec = PartitionSpec(
        PartitionField(source_id=3, field_id=1000, transform=DayTransform(), name="ts_day")
    )

    namespace = "default_namespace"
    table_name = "events"
    table_identifier = f"{namespace}.{table_name}"

    try:
        catalog.create_namespace(namespace)
    except Exception:
        pass # Namespace might already exist

    logger.info(f"Creating Iceberg Table '{table_identifier}'...")
    try:
        # Create the table
        table = catalog.create_table(
            identifier=table_identifier,
            schema=schema,
            partition_spec=partition_spec,
            location=f"s3://my-warehouse/{namespace}/{table_name}"
        )
        logger.info("Table created successfully.")
    except TableAlreadyExistsError:
        logger.info("Table already exists. Loading table...")
        table = catalog.load_table(table_identifier)

    logger.info("Table Metadata:")
    logger.info(f"Location: {table.location()}")
    logger.info(f"Schema: {table.schema()}")
    
    # Simulate appending data using PyArrow
    logger.info("\nSimulating Data Ingestion...")
    
    # Create PyArrow Table matching the schema
    df = pa.Table.from_pydict({
        'id': [1, 2],
        'event_name': ['click', 'view'],
        'ts': [
            pa.scalar('2023-10-01T10:00:00Z', type=pa.timestamp('us')),
            pa.scalar('2023-10-01T10:05:00Z', type=pa.timestamp('us'))
        ]
    })
    
    try:
        # Append data to the Iceberg table
        table.append(df)
        logger.info(f"Successfully appended {len(df)} records.")
        
        # Reload table to get new snapshot
        table.refresh()
        current_snapshot = table.current_snapshot()
        if current_snapshot:
            logger.info(f"Current Snapshot ID: {current_snapshot.snapshot_id}")
            logger.info(f"Manifest List: {current_snapshot.manifest_list}")
    except Exception as e:
        logger.error(f"Failed to append data: {e}")

if __name__ == "__main__":
    manage_iceberg()
