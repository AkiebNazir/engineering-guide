/*
FOUNDATION LEVEL 02 - Real fields in, real fields out
=========================================================
REST's level 02 was "JSON in and out". This is the same lesson, and the point is
how little there is to do: the generated `CreateOrderRequest` and
`CreateOrderResponse` structs ARE the JSON-in / JSON-out step. There is no
`json.Unmarshal`, no `map[string]any`, no "did they spell it gift_wrap or
giftWrap", no schema validation code to write for the SHAPE of the data.

WHAT REPLACED WHAT

	REST                                  gRPC
	----------------------------------    -------------------------------------
	json.Unmarshal(body, &v)              req is already a typed struct
	v["quantity"] may be missing/nil      req.GetQuantity() is always an int32
	runtime type assertion panics         wrong field name = a COMPILE error
	json.Marshal(responseStruct)          return a typed response message

You will learn
  - how .proto types map to Go: string->string, int32->int32, int64->int64,
    double->float64, bool->bool, repeated->a slice
  - naming: `gift_wrap` in the .proto becomes `GiftWrap` in Go and stays
    `gift_wrap` in Python - the generator applies each language's convention
  - every field has a zero value and is never missing: unset string is "", unset
    numeric is 0, unset bool is false, unset repeated is a nil slice
  - always use the generated GetX() accessors: they are nil-safe, so a nil
    message reads as zero values instead of panicking
  - SHAPE validation is free, but BUSINESS validation is still yours: protobuf
    guarantees Quantity is an int32, never that it is positive (level 06)

Run it   go run ./gRPC/Foundation/golang/02_unary_request_and_response_fields
*/
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"strings"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"dsapractice/api/gRPC/Foundation/golang/pb/orderspb"
)

var pricesCents = map[string]int64{"KEYB-01": 4999, "MOUSE-02": 1999}

const giftWrapCents int64 = 350

type orderServer struct {
	orderspb.UnimplementedOrderServiceServer
}

func (s *orderServer) CreateOrder(ctx context.Context, req *orderspb.CreateOrderRequest) (*orderspb.CreateOrderResponse, error) {
	// Every field is guaranteed to EXIST and to have the declared type. So this
	// handler never checks "is quantity present" or "is it a number" - only
	// whether the value makes business sense, which protobuf cannot know.
	fmt.Printf("  [server] sku=%q quantity=%d currency=%q gift_wrap=%v\n",
		req.GetSku(), req.GetQuantity(), req.GetCurrency(), req.GetGiftWrap())

	unit := pricesCents[req.GetSku()] // a missing map key gives 0, protobuf's zero value too
	total := unit * int64(req.GetQuantity())

	currency := req.GetCurrency()
	if currency == "" { // "" is the zero value, so this is the "not specified" default
		currency = "EUR"
	}

	res := &orderspb.CreateOrderResponse{
		OrderId:    "ord-" + strings.ToLower(req.GetSku()),
		TotalCents: total,
		Currency:   currency,
		// A `repeated string` is just a []string in Go - append to it normally.
		Notes: []string{fmt.Sprintf("%d x %s @ %dc", req.GetQuantity(), req.GetSku(), unit)},
	}
	if req.GetGiftWrap() {
		res.TotalCents += giftWrapCents
		res.Notes = append(res.Notes, fmt.Sprintf("gift wrap +%dc", giftWrapCents))
	}
	return res, nil
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	srv := grpc.NewServer()
	orderspb.RegisterOrderServiceServer(srv, &orderServer{})
	go srv.Serve(ln)
	defer srv.Stop()

	conn, err := grpc.NewClient(ln.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	client := orderspb.NewOrderServiceClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// --- all fields set explicitly ---
	res, err := client.CreateOrder(ctx, &orderspb.CreateOrderRequest{
		Sku: "KEYB-01", Quantity: 2, Currency: "USD", GiftWrap: true,
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("order_id    : %q\n", res.GetOrderId())
	fmt.Printf("total_cents : %d   (2 x 4999 + 350 gift wrap)\n", res.GetTotalCents())
	fmt.Printf("currency    : %q\n", res.GetCurrency())
	fmt.Printf("notes       : %v\n", res.GetNotes())
	if res.GetTotalCents() != 2*4999+giftWrapCents || res.GetCurrency() != "USD" || len(res.GetNotes()) != 2 {
		panic("FAILED")
	}

	// --- only some fields set: the rest are zero values, never missing ---
	res, err = client.CreateOrder(ctx, &orderspb.CreateOrderRequest{Sku: "MOUSE-02", Quantity: 1})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("\nwith currency and gift_wrap left unset:")
	fmt.Printf("  currency defaulted by the SERVER to %q (it received \"\")\n", res.GetCurrency())
	fmt.Printf("  gift_wrap arrived as false, so notes has %d entry\n", len(res.GetNotes()))
	if res.GetCurrency() != "EUR" || len(res.GetNotes()) != 1 {
		panic("FAILED")
	}

	// --- the zero-value rule, on a locally built message ---
	empty := &orderspb.CreateOrderRequest{}
	fmt.Println("\nan entirely empty CreateOrderRequest reads as:")
	fmt.Printf("  sku=%q quantity=%d currency=%q gift_wrap=%v\n",
		empty.GetSku(), empty.GetQuantity(), empty.GetCurrency(), empty.GetGiftWrap())
	if empty.GetSku() != "" || empty.GetQuantity() != 0 || empty.GetGiftWrap() {
		panic("FAILED")
	}
	if (&orderspb.CreateOrderResponse{}).GetNotes() != nil {
		panic("FAILED")
	}

	// The nil-safety of the accessors, which is why you use them everywhere:
	var nilReq *orderspb.CreateOrderRequest
	fmt.Printf("\na NIL *CreateOrderRequest still reads safely: sku=%q quantity=%d\n",
		nilReq.GetSku(), nilReq.GetQuantity())
	fmt.Println("  -> nilReq.Sku would panic; nilReq.GetSku() returns the zero value")
	if nilReq.GetSku() != "" {
		panic("FAILED")
	}

	// And the compile-time half: `empty.GiftWrap` is correct Go, while
	// `empty.gift_wrap` or `empty.Giftwrap` would not compile at all - the
	// mistake that becomes a runtime nil in REST is caught by `go build` here.
	fmt.Println("\nmisspelling a field is a COMPILE error in Go, not a runtime nil")

	fmt.Println("OK")
}
