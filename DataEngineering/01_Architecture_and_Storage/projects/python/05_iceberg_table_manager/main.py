class MockIcebergTable:
    def __init__(self, name, schema, partition_spec):
        self.name = name
        self.schema = schema
        self.partition_spec = partition_spec
        self.data = []
        self.metadata_versions = 0
    
    def append_data(self, records):
        self.data.extend(records)
        self.metadata_versions += 1
        print(f"Appended {len(records)} records. New metadata version v{self.metadata_versions}.")
        
    def show_metadata(self):
        print(f"\nTable: {self.name}")
        print(f"Schema: {self.schema}")
        print(f"Partitioning: {self.partition_spec}")
        print(f"Total Records: {len(self.data)}")
        print(f"Metadata Version: v{self.metadata_versions}")

def manage_iceberg():
    print("Initializing Mock Iceberg Catalog...")
    
    schema = {
        'id': 'long',
        'event_name': 'string',
        'ts': 'timestamp'
    }
    
    partition_spec = ['day(ts)']
    
    print("Creating Iceberg Table 'events'...")
    table = MockIcebergTable("events", schema, partition_spec)
    table.show_metadata()
    
    print("\nSimulating Data Ingestion...")
    batch_1 = [
        {'id': 1, 'event_name': 'click', 'ts': '2023-10-01T10:00:00Z'},
        {'id': 2, 'event_name': 'view', 'ts': '2023-10-01T10:05:00Z'}
    ]
    table.append_data(batch_1)
    
    batch_2 = [
        {'id': 3, 'event_name': 'purchase', 'ts': '2023-10-02T11:00:00Z'}
    ]
    table.append_data(batch_2)
    
    table.show_metadata()

if __name__ == "__main__":
    # In a real environment, you might use pyiceberg:
    # from pyiceberg.catalog import load_catalog
    # catalog = load_catalog("default")
    manage_iceberg()
