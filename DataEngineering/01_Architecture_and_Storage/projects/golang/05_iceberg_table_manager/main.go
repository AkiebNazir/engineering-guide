package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/glue"
	"github.com/aws/aws-sdk-go-v2/service/glue/types"
)

// IcebergManager handles operations related to Iceberg tables in AWS Glue Data Catalog.
type IcebergManager struct {
	glueClient *glue.Client
	database   string
}

// NewIcebergManager creates a new manager using the default AWS configuration.
func NewIcebergManager(ctx context.Context, region, database string) (*IcebergManager, error) {
	cfg, err := config.LoadDefaultConfig(ctx, config.WithRegion(region))
	if err != nil {
		return nil, fmt.Errorf("unable to load SDK config: %w", err)
	}

	return &IcebergManager{
		glueClient: glue.NewFromConfig(cfg),
		database:   database,
	}, nil
}

// CreateIcebergTable creates an Apache Iceberg table definition in the Glue Data Catalog.
func (m *IcebergManager) CreateIcebergTable(ctx context.Context, tableName string, location string) error {
	log.Printf("Creating Iceberg table '%s' in database '%s'...\n", tableName, m.database)

	// Define columns according to Iceberg schema requirements
	columns := []types.Column{
		{Name: aws.String("id"), Type: aws.String("bigint")},
		{Name: aws.String("event_name"), Type: aws.String("string")},
		{Name: aws.String("ts"), Type: aws.String("timestamp")},
	}

	// Iceberg tables in Glue require specific parameters
	tableInput := &types.TableInput{
		Name:        aws.String(tableName),
		TableType:   aws.String("EXTERNAL_TABLE"),
		Parameters: map[string]string{
			"table_type":                  "ICEBERG",
			"format":                      "parquet",
			"metadata_location":           fmt.Sprintf("%s/metadata/00000-%s.metadata.json", location, time.Now().Format("20060102150405")),
			"classification":              "iceberg",
		},
		StorageDescriptor: &types.StorageDescriptor{
			Columns:      columns,
			Location:     aws.String(location),
			InputFormat:  aws.String("org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"),
			OutputFormat: aws.String("org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"),
			SerdeInfo: &types.SerDeInfo{
				SerializationLibrary: aws.String("org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"),
			},
		},
	}

	_, err := m.glueClient.CreateTable(ctx, &glue.CreateTableInput{
		DatabaseName: aws.String(m.database),
		TableInput:   tableInput,
	})

	if err != nil {
		return fmt.Errorf("failed to create Glue table: %w", err)
	}

	log.Printf("Successfully created Iceberg table metadata for '%s'\n", tableName)
	return nil
}

// GetTableMetadata retrieves the metadata location and details of the Iceberg table.
func (m *IcebergManager) GetTableMetadata(ctx context.Context, tableName string) error {
	log.Printf("Retrieving metadata for table '%s'...\n", tableName)
	
	output, err := m.glueClient.GetTable(ctx, &glue.GetTableInput{
		DatabaseName: aws.String(m.database),
		Name:         aws.String(tableName),
	})

	if err != nil {
		return fmt.Errorf("failed to get table metadata: %w", err)
	}

	table := output.Table
	fmt.Printf("\n--- Iceberg Table Metadata ---\n")
	fmt.Printf("Name: %s\n", *table.Name)
	fmt.Printf("Location: %s\n", *table.StorageDescriptor.Location)
	fmt.Printf("Type: %s\n", table.Parameters["table_type"])
	fmt.Printf("Current Metadata Location: %s\n", table.Parameters["metadata_location"])
	fmt.Printf("Columns:\n")
	for _, col := range table.StorageDescriptor.Columns {
		fmt.Printf("  - %s (%s)\n", *col.Name, *col.Type)
	}
	fmt.Println("------------------------------")
	
	return nil
}

func main() {
	// Setup context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	region := "us-east-1"
	database := "default_namespace"
	tableName := "events_iceberg"
	s3Location := "s3://my-warehouse/default_namespace/events"

	manager, err := NewIcebergManager(ctx, region, database)
	if err != nil {
		log.Fatalf("Error initializing manager: %v", err)
	}

	// This code simulates creating the Iceberg table in AWS Glue Metastore.
	// Note: Requires valid AWS credentials with Glue permissions to execute successfully.
	log.Println("Starting Iceberg Table Manager (AWS Glue integration)...")
	
	err = manager.CreateIcebergTable(ctx, tableName, s3Location)
	if err != nil {
		log.Printf("Note: Create table failed (expected if AWS credentials are not configured): %v\n", err)
	}

	err = manager.GetTableMetadata(ctx, tableName)
	if err != nil {
		log.Printf("Note: Get table metadata failed (expected if table doesn't exist): %v\n", err)
	}
	
	log.Println("Execution completed.")
}
