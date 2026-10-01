/*
FOUNDATION LEVEL 11 (CAPSTONE) - One realistic schema, used end to end
=======================================================================
Everything from levels 00-10, combined into one schema you could defend in a
design review. ../../proto/l11_capstone.proto has nested messages (02),
repeated fields (03), an `optional` field for real presence (04), an enum
(05), and a documented evolution log with a `reserved` number (06).

This program and its Python twin both read and write the SAME file format, so
the pair of them is a complete, if tiny, polyglot system: a Python service
writes shipments, a Go service consumes them (and the other way round), and
neither one knows the other's language. That is the whole point of the folder,
demonstrated once properly.

You will learn
  - how the pieces combine in a schema you would actually ship
  - why a top-level "file" message with a schema_version beats a bare list
  - doing real work with decoded data: filtering, grouping, summing
  - checking presence (a nil *int64) to tell "not delivered yet" from
    "delivered at time 0"
  - the size win over equivalent JSON, measured on realistic data
  - that the Python twin reads this exact file, and writes one this reads back

Run it   go run ./Protobuf/Foundation/golang/11_capstone_realistic_schema
Then     python Protobuf/Foundation/python/11_capstone_realistic_schema.py
*/
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"google.golang.org/protobuf/proto"

	"dsapractice/api/Protobuf/Foundation/golang/pb/l11"
)

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

const schemaVersion = 2 // matches the evolution log in ../../proto/l11_capstone.proto

// Shared with the Python twin. Each language writes its own file and reads
// the other's if it is present.
const (
	sharedDirName = "protobuf_foundation_capstone"
	pyFile        = "shipments_from_python.pb"
	goFile        = "shipments_from_go.pb"
)

// buildShipmentFile builds a realistic payload, exercising every construct in
// the schema. It is the same data the Python twin builds.
func buildShipmentFile() *l11.ShipmentFile {
	return &l11.ShipmentFile{
		SchemaVersion: schemaVersion,
		Shipments: []*l11.Shipment{
			{
				// A delivered shipment: DeliveredUnixMillis is set, so presence is on.
				ShipmentId: "SHP-1001",
				Carrier:    l11.Carrier_CARRIER_DHL, // enum (level 05)
				Destination: &l11.Address{ // nested (level 02)
					Line1: "12 Dean St", City: "Oslo", CountryCode: "NO",
				},
				Items: []*l11.LineItem{ // repeated message (level 03)
					{Sku: "WIDGET-1", Qty: 2, UnitPriceCents: 1999},
					{Sku: "CABLE-3", Qty: 1, UnitPriceCents: 499},
				},
				Tags:                []string{"priority", "signed-for"}, // repeated scalar (03)
				DeliveredUnixMillis: proto.Int64(1_700_000_000_000),     // optional (level 04)
			},
			{
				// In transit. DeliveredUnixMillis is deliberately left nil - that
				// absence IS the data, and level 04 is why it survives the trip.
				ShipmentId:  "SHP-1002",
				Carrier:     l11.Carrier_CARRIER_POSTNORD,
				Destination: &l11.Address{Line1: "1 Storgata", City: "Bergen", CountryCode: "NO"},
				Items:       []*l11.LineItem{{Sku: "WIDGET-1", Qty: 10, UnitPriceCents: 1999}},
				Tags:        []string{"fragile"},
			},
			{
				// Carrier left unset, to show *_UNSPECIFIED in action.
				ShipmentId:  "SHP-1003",
				Destination: &l11.Address{Line1: "9 Karl Johans gate", City: "Oslo", CountryCode: "NO"},
				Items:       []*l11.LineItem{{Sku: "CABLE-3", Qty: 3, UnitPriceCents: 499}},
			},
		},
	}
}

// The same data as plain Go structs with JSON tags, purely to size the JSON
// comparison. The shape (and key order) mirrors the Python twin's dicts.
type jsonAddress struct {
	Line1       string `json:"line1"`
	City        string `json:"city"`
	CountryCode string `json:"country_code"`
}
type jsonItem struct {
	Sku            string `json:"sku"`
	Qty            int32  `json:"qty"`
	UnitPriceCents int64  `json:"unit_price_cents"`
}
type jsonShipment struct {
	ShipmentID          string      `json:"shipment_id"`
	Carrier             string      `json:"carrier"`
	Destination         jsonAddress `json:"destination"`
	Items               []jsonItem  `json:"items"`
	Tags                []string    `json:"tags"`
	DeliveredUnixMillis *int64      `json:"delivered_unix_millis,omitempty"`
}
type jsonFile struct {
	SchemaVersion int32          `json:"schema_version"`
	Shipments     []jsonShipment `json:"shipments"`
}

func asPlainJSON(doc *l11.ShipmentFile) []byte {
	out := jsonFile{SchemaVersion: doc.GetSchemaVersion()}
	for _, s := range doc.GetShipments() {
		js := jsonShipment{
			ShipmentID: s.GetShipmentId(),
			Carrier:    s.GetCarrier().String(),
			Destination: jsonAddress{
				Line1: s.GetDestination().GetLine1(), City: s.GetDestination().GetCity(),
				CountryCode: s.GetDestination().GetCountryCode(),
			},
			Items:               []jsonItem{},
			Tags:                append([]string{}, s.GetTags()...),
			DeliveredUnixMillis: s.DeliveredUnixMillis,
		}
		for _, it := range s.GetItems() {
			js.Items = append(js.Items, jsonItem{it.GetSku(), it.GetQty(), it.GetUnitPriceCents()})
		}
		out.Shipments = append(out.Shipments, js)
	}
	data, err := json.Marshal(out)
	must(err == nil, "json")
	return data
}

func delivered(s *l11.Shipment) string {
	if s.DeliveredUnixMillis == nil {
		return "not delivered"
	}
	return fmt.Sprint(*s.DeliveredUnixMillis)
}

func main() {
	fmt.Println("== 1. build the payload ==")
	doc := buildShipmentFile()
	fmt.Printf("  schema_version = %d, %d shipments\n", doc.GetSchemaVersion(), len(doc.GetShipments()))
	for _, s := range doc.GetShipments() {
		fmt.Printf("    %s  %-18s %-7s items=%d delivered=%s\n", s.GetShipmentId(), s.GetCarrier(),
			s.GetDestination().GetCity(), len(s.GetItems()), delivered(s))
	}

	fmt.Println("\n== 2. encode, and compare against JSON ==")
	encoded, err := proto.Marshal(doc)
	must(err == nil, "marshal")
	asJSON := asPlainJSON(doc)
	fmt.Printf("  protobuf : %4d bytes\n", len(encoded))
	fmt.Printf("  JSON     : %4d bytes (compact, no whitespace)\n", len(asJSON))
	fmt.Printf("  -> %d%% smaller. On realistic nested data the gap is much wider\n",
		100-(100*len(encoded)+len(asJSON)/2)/len(asJSON))
	fmt.Println("     than level 00's single field, because every repeated element in")
	fmt.Println("     JSON re-sends all of its key names as text.")
	must(len(encoded) < len(asJSON), "protobuf is smaller")

	fmt.Println("\n== 3. write it, then read it back as a separate step ==")
	shared := filepath.Join(os.TempDir(), sharedDirName)
	must(os.MkdirAll(shared, 0o755) == nil, "create shared dir")
	path := filepath.Join(shared, goFile)
	must(os.WriteFile(path, encoded, 0o644) == nil, "write")
	raw, err := os.ReadFile(path)
	must(err == nil, "read")
	reloaded := &l11.ShipmentFile{}
	must(proto.Unmarshal(raw, reloaded) == nil, "unmarshal")
	fmt.Printf("  wrote and re-read %s (%d bytes)\n", goFile, len(raw))
	must(proto.Equal(reloaded, doc), "the whole document round-trips exactly")
	fmt.Println("  proto.Equal(reloaded, original) -> true, field for field.")

	fmt.Println("\n== 4. presence survived, and it matters ==")
	var flags []bool
	for _, s := range reloaded.GetShipments() {
		has := s.DeliveredUnixMillis != nil
		flags = append(flags, has)
		fmt.Printf("    %s: DeliveredUnixMillis != nil -> %v   (GetDeliveredUnixMillis() = %d)\n",
			s.GetShipmentId(), has, s.GetDeliveredUnixMillis())
	}
	must(len(flags) == 3 && flags[0] && !flags[1] && !flags[2], "presence per shipment")
	fmt.Println("  note the getter returns 0 for both in-transit shipments - GetX() is never")
	fmt.Println("  a presence check. Had this been a plain int64, SHP-1002 would be")
	fmt.Println("  indistinguishable from 'delivered at midnight, 1 January 1970' (level 04).")

	fmt.Println("\n== 5. doing real work with the decoded data ==")
	// Ordinary application code. The decoded message is just a Go struct.
	var totalCents int64
	byCarrier := map[string]int{}
	var pending []string
	widgetQty := int32(0)
	for _, s := range reloaded.GetShipments() {
		for _, it := range s.GetItems() {
			totalCents += int64(it.GetQty()) * it.GetUnitPriceCents()
			if it.GetSku() == "WIDGET-1" {
				widgetQty += it.GetQty()
			}
		}
		byCarrier[s.GetCarrier().String()]++
		if s.DeliveredUnixMillis == nil {
			pending = append(pending, s.GetShipmentId())
		}
	}
	fmt.Printf("  total value across all shipments : %.2f\n", float64(totalCents)/100)
	must(totalCents == 2*1999+499+10*1999+3*499, "total")
	carriers := make([]string, 0, len(byCarrier))
	for c := range byCarrier {
		carriers = append(carriers, c)
	}
	sort.Strings(carriers)
	fmt.Print("  shipments per carrier            :")
	for _, c := range carriers {
		fmt.Printf(" %s=%d", c, byCarrier[c])
	}
	fmt.Println()
	must(byCarrier["CARRIER_UNSPECIFIED"] == 1, "SHP-1003 never had a carrier set")
	fmt.Printf("  still in transit                 : %v\n", pending)
	must(len(pending) == 2 && pending[0] == "SHP-1002" && pending[1] == "SHP-1003", "pending")
	fmt.Printf("  total WIDGET-1 units             : %d\n", widgetQty)
	must(widgetQty == 12, "widget qty")

	fmt.Println("\n== 6. the evolution log is part of the design ==")
	fmt.Println("  ../../proto/l11_capstone.proto records, in comments beside the fields:")
	fmt.Println("    v1 : fields 1-5")
	fmt.Println("    v2 : added optional delivered_unix_millis (6)")
	fmt.Println("    v2 : deleted tracking_url (7) -> `reserved 7; reserved \"tracking_url\";`")
	reserved := (&l11.Shipment{}).ProtoReflect().Descriptor().ReservedRanges()
	must(reserved.Len() == 1 && reserved.Get(0)[0] == 7, "7 is reserved in the compiled descriptor")
	fmt.Println("  (and the compiled descriptor agrees: number 7 is reserved)")
	fmt.Println("  A v1 reader handed this file ignores field 6 and keeps it on re-encode")
	fmt.Println("  (level 06). A v3 that needs a new field appends number 8 - never 7.")
	fmt.Printf("  The payload also states its own version (%d), which costs 2 bytes and\n",
		reloaded.GetSchemaVersion())
	fmt.Println("  tells a future reader which rules produced these bytes.")

	fmt.Println("\n== 7. the Python twin's file, read by Go ==")
	if data, err := os.ReadFile(filepath.Join(shared, pyFile)); err == nil {
		fromPy := &l11.ShipmentFile{}
		must(proto.Unmarshal(data, fromPy) == nil, "decode Python's file")
		fmt.Printf("  found %s written by a real Python run:\n", pyFile)
		fmt.Printf("    schema_version=%d, %d shipments\n", fromPy.GetSchemaVersion(), len(fromPy.GetShipments()))
		var pyPending []string
		for _, s := range fromPy.GetShipments() {
			fmt.Printf("      %s  %-18s %s items=%d\n", s.GetShipmentId(), s.GetCarrier(),
				s.GetDestination().GetCity(), len(s.GetItems()))
			// The real test of a shared format: Go understands Python's presence bits.
			if s.DeliveredUnixMillis == nil {
				pyPending = append(pyPending, s.GetShipmentId())
			}
		}
		must(fromPy.GetSchemaVersion() == schemaVersion && len(fromPy.GetShipments()) > 0, "python file content")
		fmt.Printf("    in transit, per Go's reading of Python's bytes: %v\n", pyPending)
		// Both twins build the same data, so the documents are equal - and
		// for this message the bytes happen to be identical too.
		fmt.Printf("    proto.Equal(Python's document, ours) -> %v\n", proto.Equal(fromPy, doc))
		fmt.Println("  a Python process wrote that file. Nothing was converted or negotiated.")
	} else {
		fmt.Printf("  %s is not there yet. Run the Python twin:\n", pyFile)
		fmt.Println("      python Protobuf/Foundation/python/11_capstone_realistic_schema.py")
		fmt.Println("  It will decode the file this program just wrote, and write its own;")
		fmt.Println("  re-run this program to decode Python's shipments here.")
		fmt.Printf("  (both languages exchange files under %s)\n", shared)
	}

	fmt.Println("\n== where this leaves you ==")
	fmt.Println("  You can now design a protobuf schema, evolve it without breaking")
	fmt.Println("  anyone, and move it between languages. Level 12 is the one-page")
	fmt.Println("  bridge to gRPC; level 13 is the optional wire-format deep dive.")

	fmt.Println("\nOK")
}
