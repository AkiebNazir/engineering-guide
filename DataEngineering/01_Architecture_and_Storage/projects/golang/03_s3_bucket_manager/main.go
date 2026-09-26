package main

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"log"
	"os"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
	"github.com/aws/smithy-go"
)

// S3Manager struct wraps the S3 client to provide high-level methods.
type S3Manager struct {
	client *s3.Client
	region string
}

// NewS3Manager initializes a new S3 client using the default AWS configuration chain.
func NewS3Manager(ctx context.Context, region string) (*S3Manager, error) {
	cfg, err := config.LoadDefaultConfig(ctx, config.WithRegion(region))
	if err != nil {
		return nil, fmt.Errorf("unable to load SDK config: %w", err)
	}

	return &S3Manager{
		client: s3.NewFromConfig(cfg),
		region: region,
	}, nil
}

// CreateBucket creates a new S3 bucket.
func (m *S3Manager) CreateBucket(ctx context.Context, bucketName string) error {
	input := &s3.CreateBucketInput{
		Bucket: aws.String(bucketName),
	}

	// For regions other than us-east-1, a LocationConstraint is required.
	if m.region != "us-east-1" {
		input.CreateBucketConfiguration = &types.CreateBucketConfiguration{
			LocationConstraint: types.BucketLocationConstraint(m.region),
		}
	}

	_, err := m.client.CreateBucket(ctx, input)
	if err != nil {
		var bnf *types.BucketAlreadyExists
		if errors.As(err, &bnf) {
			log.Printf("Bucket %s already exists.", bucketName)
			return nil
		}
		var bof *types.BucketAlreadyOwnedByYou
		if errors.As(err, &bof) {
			log.Printf("Bucket %s is already owned by you.", bucketName)
			return nil
		}
		return fmt.Errorf("failed to create bucket: %w", err)
	}
	log.Printf("Successfully created bucket: %s\n", bucketName)
	return nil
}

// UploadObject uploads data to the specified bucket and key.
func (m *S3Manager) UploadObject(ctx context.Context, bucketName, objectKey string, data []byte) error {
	_, err := m.client.PutObject(ctx, &s3.PutObjectInput{
		Bucket:               aws.String(bucketName),
		Key:                  aws.String(objectKey),
		Body:                 bytes.NewReader(data),
		ServerSideEncryption: types.ServerSideEncryptionAes256,
	})
	if err != nil {
		return fmt.Errorf("failed to upload object: %w", err)
	}
	log.Printf("Successfully uploaded s3://%s/%s\n", bucketName, objectKey)
	return nil
}

// ListObjects returns a slice of object metadata for the given bucket.
func (m *S3Manager) ListObjects(ctx context.Context, bucketName string) ([]types.Object, error) {
	var objects []types.Object
	paginator := s3.NewListObjectsV2Paginator(m.client, &s3.ListObjectsV2Input{
		Bucket: aws.String(bucketName),
	})

	for paginator.HasMorePages() {
		page, err := paginator.NextPage(ctx)
		if err != nil {
			return nil, fmt.Errorf("failed to get page: %w", err)
		}
		objects = append(objects, page.Contents...)
	}

	log.Printf("Found %d objects in bucket %s\n", len(objects), bucketName)
	return objects, nil
}

// ReadObject reads and returns the contents of an S3 object.
func (m *S3Manager) ReadObject(ctx context.Context, bucketName, objectKey string) ([]byte, error) {
	out, err := m.client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(bucketName),
		Key:    aws.String(objectKey),
	})
	if err != nil {
		var nsk *types.NoSuchKey
		if errors.As(err, &nsk) {
			return nil, fmt.Errorf("object not found: %s", objectKey)
		}
		var apiErr smithy.APIError
		if errors.As(err, &apiErr) {
			return nil, fmt.Errorf("API error: %s - %s", apiErr.ErrorCode(), apiErr.ErrorMessage())
		}
		return nil, fmt.Errorf("failed to get object: %w", err)
	}
	defer out.Body.Close()

	data, err := io.ReadAll(out.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read object body: %w", err)
	}

	return data, nil
}

func main() {
	// Setup context with timeout for overall execution safety
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	region := "us-east-1"
	bucketName := os.Getenv("S3_BUCKET_NAME")
	if bucketName == "" {
		bucketName = "my-production-data-lake-12345"
	}

	log.Println("Initializing S3 Manager...")
	manager, err := NewS3Manager(ctx, region)
	if err != nil {
		log.Fatalf("Failed to initialize S3 manager: %v", err)
	}

	// 1. Create Bucket
	if err := manager.CreateBucket(ctx, bucketName); err != nil {
		log.Printf("Warning: CreateBucket failed: %v", err)
		// We can optionally return here, but perhaps the bucket already exists and we lack permissions to create,
		// yet have permissions to read/write.
	}

	// 2. Upload Object
	objectKey := "raw/data.txt"
	content := []byte("Production data content for our S3 bucket in Go")
	if err := manager.UploadObject(ctx, bucketName, objectKey, content); err != nil {
		log.Printf("Error uploading object: %v", err)
	}

	// 3. List Objects
	objects, err := manager.ListObjects(ctx, bucketName)
	if err != nil {
		log.Printf("Error listing objects: %v", err)
	} else {
		fmt.Println("\nObjects found:")
		for _, obj := range objects {
			fmt.Printf("- %s (Size: %d bytes, Last Modified: %v)\n", *obj.Key, *obj.Size, *obj.LastModified)
		}
	}

	// 4. Read Object
	data, err := manager.ReadObject(ctx, bucketName, objectKey)
	if err != nil {
		log.Printf("Error reading object: %v", err)
	} else {
		fmt.Printf("\nObject Content: %s\n", string(data))
	}
}
