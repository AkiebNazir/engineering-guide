import boto3
from botocore.exceptions import ClientError

def create_or_update_glue_table(glue_client, database_name, table_name):
    """
    Creates or updates an AWS Glue Data Catalog table representing our metadata.
    AWS Glue serves as a standard metadata catalog in many data lakes.
    """
    table_input = {
        'Name': table_name,
        'Description': 'Daily aggregated sales facts.',
        'Owner': 'data_engineering@company.com',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'date', 'Type': 'date', 'Comment': 'Transaction date'},
                {'Name': 'total_amount', 'Type': 'double', 'Comment': 'Sum of sales'}
            ],
            'Location': f's3://my-data-lake/warehouse/{table_name}/',
            'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
            }
        },
        'TableType': 'EXTERNAL_TABLE',
        'Parameters': {
            'classification': 'parquet',
            'has_encrypted_data': 'true'
        }
    }

    try:
        # Check if database exists, create if not
        try:
            glue_client.get_database(Name=database_name)
        except glue_client.exceptions.EntityNotFoundException:
            print(f"Database {database_name} not found. Creating...")
            glue_client.create_database(DatabaseInput={'Name': database_name})

        # Check if table exists
        print(f"Checking if table {database_name}.{table_name} exists...")
        glue_client.get_table(DatabaseName=database_name, Name=table_name)
        
        # If it exists, update it
        print("Table exists. Updating metadata...")
        glue_client.update_table(
            DatabaseName=database_name,
            TableInput=table_input
        )
        print("Metadata catalog successfully updated.")
    except glue_client.exceptions.EntityNotFoundException:
        # If it doesn't exist, create it
        print("Table not found. Creating new table in catalog...")
        glue_client.create_table(
            DatabaseName=database_name,
            TableInput=table_input
        )
        print("Metadata catalog successfully created.")
    except ClientError as e:
        print(f"Failed to interact with AWS Glue Catalog: {e}")
        # Note: If no AWS credentials are found, this will fail gracefully.
        print("\nNote: AWS credentials are required to actually execute this against a real account.")

def main():
    # Initialize boto3 client for AWS Glue
    # Real-world usage requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables
    # or IAM roles attached to the compute instance.
    print("Connecting to AWS Glue Data Catalog...")
    glue_client = boto3.client('glue', region_name='us-east-1')
    
    database_name = 'sales_mart'
    table_name = 'fct_sales'
    
    create_or_update_glue_table(glue_client, database_name, table_name)

if __name__ == "__main__":
    main()
