package main

import (
	"encoding/json"
	"fmt"
	"os"
	"time"
)

type IcebergMetadata struct {
	FormatVersion int        `json:"format-version"`
	TableUUID     string     `json:"table-uuid"`
	Location      string     `json:"location"`
	LastUpdatedMs int64      `json:"last-updated-ms"`
	CurrentSnapID int64      `json:"current-snapshot-id"`
	Snapshots     []Snapshot `json:"snapshots"`
}

type Snapshot struct {
	SnapshotID int64  `json:"snapshot-id"`
	Manifest   string `json:"manifest-list"`
}

func main() {
	metadataFile := "v1.metadata.json"

	meta := IcebergMetadata{
		FormatVersion: 2,
		TableUUID:     "d2243d4f-561b-4b2a-87b6-1ebbf5511b81",
		Location:      "s3://warehouse/tables/my_iceberg_table",
		LastUpdatedMs: time.Now().UnixMilli(),
		CurrentSnapID: 1001,
		Snapshots: []Snapshot{
			{SnapshotID: 1001, Manifest: "snap-1001-manifest.avro"},
		},
	}

	data, err := json.MarshalIndent(meta, "", "  ")
	if err != nil {
		panic(err)
	}

	if err := os.WriteFile(metadataFile, data, 0644); err != nil {
		panic(err)
	}

	fmt.Println("Iceberg table metadata mock written to:", metadataFile)
}
