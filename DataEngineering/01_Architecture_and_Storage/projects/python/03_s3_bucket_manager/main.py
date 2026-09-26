import os
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class S3Manager:
    """A production-grade wrapper around boto3 S3 operations."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initializes the S3 client. In production, credentials should be configured 
        via IAM roles, ~/.aws/credentials, or environment variables.
        """
        # Note: boto3 automatically uses available credentials
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.region = region_name

    def create_bucket(self, bucket_name: str) -> bool:
        """Creates an S3 bucket in the specified region."""
        try:
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            logger.info(f"Successfully created bucket: {bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e.response['Error']['Message']}")
            return False

    def upload_file(self, bucket_name: str, object_key: str, content: bytes) -> bool:
        """Uploads bytes content to an S3 bucket."""
        try:
            self.s3_client.put_object(
                Bucket=bucket_name, 
                Key=object_key, 
                Body=content,
                ServerSideEncryption='AES256' # Production best practice
            )
            logger.info(f"Successfully uploaded {object_key} to s3://{bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload object: {e.response['Error']['Message']}")
            return False

    def list_objects(self, bucket_name: str, prefix: str = '') -> list:
        """Lists objects in an S3 bucket with an optional prefix."""
        objects = []
        try:
            # Using paginator for buckets with >1000 objects
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        objects.append({
                            'Key': obj['Key'],
                            'Size': obj['Size'],
                            'LastModified': obj['LastModified']
                        })
            logger.info(f"Found {len(objects)} objects in bucket {bucket_name}")
            return objects
        except ClientError as e:
            logger.error(f"Failed to list objects: {e.response['Error']['Message']}")
            return []

    def read_object(self, bucket_name: str, object_key: str) -> bytes:
        """Reads and returns the contents of an S3 object."""
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            data = response['Body'].read()
            logger.info(f"Successfully read {len(data)} bytes from {object_key}")
            return data
        except ClientError as e:
            logger.error(f"Failed to read object {object_key}: {e.response['Error']['Message']}")
            return b""

def main():
    """
    Main function to orchestrate S3 interactions. 
    Note: To run this code against a real AWS account, ensure you have valid AWS credentials configured.
    """
    bucket_name = os.getenv("S3_BUCKET_NAME", "my-production-data-lake-12345")
    manager = S3Manager()
    
    # 1. Create a Bucket
    if manager.create_bucket(bucket_name):
        
        # 2. Upload a File
        file_content = b"Production data content for our S3 bucket"
        object_key = 'raw/data.txt'
        manager.upload_file(bucket_name, object_key, file_content)
        
        # 3. List Objects
        objects = manager.list_objects(bucket_name)
        print("\nObjects found:")
        for obj in objects:
            print(f"- {obj['Key']} (Size: {obj['Size']} bytes)")
                
        # 4. Download and Read File
        content = manager.read_object(bucket_name, object_key)
        if content:
            print(f"\nObject Content: {content.decode('utf-8')}")

if __name__ == "__main__":
    main()
