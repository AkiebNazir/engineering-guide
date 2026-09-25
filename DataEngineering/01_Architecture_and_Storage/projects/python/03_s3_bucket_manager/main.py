import boto3
from moto import mock_aws

@mock_aws
def manage_s3():
    # Setup mock AWS credentials
    import os
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

    # Create S3 client
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'my-mock-data-lake'
    
    # 1. Create a Bucket
    print(f"Creating bucket: {bucket_name}")
    s3.create_bucket(Bucket=bucket_name)
    
    # 2. Upload a File
    file_content = b"Mock data content for our S3 bucket"
    object_key = 'raw/data.txt'
    print(f"Uploading file to s3://{bucket_name}/{object_key}")
    s3.put_object(Bucket=bucket_name, Key=object_key, Body=file_content)
    
    # 3. List Objects
    print("\nListing objects in bucket:")
    response = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        for obj in response['Contents']:
            print(f"- {obj['Key']} (Size: {obj['Size']} bytes)")
            
    # 4. Download and Read File
    print(f"\nReading object {object_key}:")
    obj_response = s3.get_object(Bucket=bucket_name, Key=object_key)
    print(obj_response['Body'].read().decode('utf-8'))

if __name__ == "__main__":
    manage_s3()
