package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/glue"
	"github.com/aws/aws-sdk-go-v2/service/glue/types"
)

// ensureGlueDatabase checks if a Glue Database exists, and creates it if it doesn't.
func ensureGlueDatabase(ctx context.Context, client *glue.Client, dbName string) error {
	_, err := client.GetDatabase(ctx, &glue.GetDatabaseInput{
		Name: aws.String(dbName),
	})

	if err != nil {
		fmt.Printf("Database %s not found. Attempting to create...\n", dbName)
		_, createErr := client.CreateDatabase(ctx, &glue.CreateDatabaseInput{
			DatabaseInput: &types.DatabaseInput{
				Name: aws.String(dbName),
				Description: aws.String("Created via Golang Data Engineering App"),
			},
		})
		if createErr != nil {
			return fmt.Errorf("failed to create database: %w", createErr)
		}
		fmt.Println("Database created successfully.")
	}
	return nil
}

// createOrUpdateGlueTable defines metadata and pushes it to AWS Glue Data Catalog
func createOrUpdateGlueTable(ctx context.Context, client *glue.Client, dbName, tableName string) error {
	tableInput := &types.TableInput{
		Name:        aws.String(tableName),
		Description: aws.String("Daily aggregated sales facts."),
		Owner:       aws.String("data_engineering@company.com"),
		TableType:   aws.String("EXTERNAL_TABLE"),
		Parameters: map[string]string{
			"classification": "parquet",
			"has_encrypted_data": "true",
		},
		StorageDescriptor: &types.StorageDescriptor{
			Location: aws.String(fmt.Sprintf("s3://my-data-lake/warehouse/%s/", tableName)),
			InputFormat: aws.String("org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"),
			OutputFormat: aws.String("org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"),
			SerdeInfo: &types.SerDeInfo{
				SerializationLibrary: aws.String("org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"),
			},
			Columns: []types.Column{
				{
					Name:    aws.String("date"),
					Type:    aws.String("date"),
					Comment: aws.String("Transaction date"),
				},
				{
					Name:    aws.String("total_amount"),
					Type:    aws.String("double"),
					Comment: aws.String("Sum of sales"),
				},
			},
		},
	}

	_, err := client.GetTable(ctx, &glue.GetTableInput{
		DatabaseName: aws.String(dbName),
		Name:         aws.String(tableName),
	})

	if err != nil {
		fmt.Println("Table not found. Creating new metadata entry in Glue Catalog...")
		_, err = client.CreateTable(ctx, &glue.CreateTableInput{
			DatabaseName: aws.String(dbName),
			TableInput:   tableInput,
		})
		if err != nil {
			return fmt.Errorf("failed to create table: %w", err)
		}
	} else {
		fmt.Println("Table exists. Updating metadata entry in Glue Catalog...")
		_, err = client.UpdateTable(ctx, &glue.UpdateTableInput{
			DatabaseName: aws.String(dbName),
			TableInput:   tableInput,
		})
		if err != nil {
			return fmt.Errorf("failed to update table: %w", err)
		}
	}

	fmt.Println("Metadata catalog operation completed successfully.")
	return nil
}

func main() {
	fmt.Println("Initializing AWS Glue Data Catalog builder...")

	// Load AWS config (relies on environment variables like AWS_ACCESS_KEY_ID or IAM roles)
	cfg, err := config.LoadDefaultConfig(context.TODO(), config.WithRegion("us-east-1"))
	if err != nil {
		log.Fatalf("unable to load SDK config, %v", err)
	}

	// Create Glue client
	glueClient := glue.NewFromConfig(cfg)
	ctx := context.Background()
	dbName := "sales_mart"
	tableName := "fct_sales"

	// If AWS credentials aren't configured in the environment running this, it will error out cleanly.
	if err := ensureGlueDatabase(ctx, glueClient, dbName); err != nil {
		log.Printf("AWS Error: %v\nNote: Valid AWS credentials are required to interact with AWS Glue.", err)
		os.Exit(1)
	}

	if err := createOrUpdateGlueTable(ctx, glueClient, dbName, tableName); err != nil {
		log.Fatalf("Failed to manage table metadata: %v", err)
	}
}
