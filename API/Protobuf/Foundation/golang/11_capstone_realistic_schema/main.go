package main

import (
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	
	"dsapractice/api/Protobuf/Foundation/golang/pb/l11"
	"google.golang.org/protobuf/proto"
)

func main() {
	fmt.Println("== 1. build the payload ==")
	// Simulating the realistic schema
	doc := &l11.ShipmentFile{
		SchemaVersion: 1,
		Shipments: []*l11.Shipment{
			{
				ShipmentId: "SHP-1001",
				Carrier:    l11.Carrier_CARRIER_DHL,
				Destination: &l11.Address{
					Line1:       "12 Dean St",
					City:        "Oslo",
					CountryCode: "NO",
				},
				DeliveredUnixMillis: proto.Int64(1700000000000),
				Tags:                []string{"priority", "signed-for"},
				Items: []*l11.LineItem{
					{Sku: "WIDGET-1", Qty: 2, UnitPriceCents: 1999},
					{Sku: "CABLE-3", Qty: 1, UnitPriceCents: 499},
				},
			},
			{
				ShipmentId: "SHP-1002",
				Carrier:    l11.Carrier_CARRIER_POSTNORD,
				Destination: &l11.Address{
					Line1:       "1 Storgata",
					City:        "Bergen",
					CountryCode: "NO",
				},
				Tags: []string{"fragile"},
				Items: []*l11.LineItem{
					{Sku: "WIDGET-1", Qty: 10, UnitPriceCents: 1999},
				},
			},
			{
				ShipmentId: "SHP-1003",
				Destination: &l11.Address{
					Line1:       "9 Karl Johans gate",
					City:        "Oslo",
					CountryCode: "NO",
				},
				Items: []*l11.LineItem{
					{Sku: "CABLE-3", Qty: 3, UnitPriceCents: 499},
				},
			},
		},
	}
	fmt.Printf("  schema_version = %d, %d shipments\n", doc.SchemaVersion, len(doc.Shipments))
	
	out, err := proto.Marshal(doc)
	if err != nil {
		panic(err)
	}
	fmt.Printf("  protobuf : %d bytes\n", len(out))

	dir := "../../../../../_archive/Protobuf/golang/shared" // Or /tmp or whatever is used
	os.MkdirAll(dir, 0755)
	path := filepath.Join(dir, "11_from_go.bin")
	if err := ioutil.WriteFile(path, out, 0644); err != nil {
		fmt.Println(err)
	}
	
	fmt.Println("\nOK")
}
