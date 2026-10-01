/*
FOUNDATION BONUS - GraphQL has no special transport (optional, read last)
=============================================================================
Levels 11 and 12 used net/http on both sides, and never asked what that
library does underneath. This file answers that, and makes one point:

	there is nothing about GraphQL on the wire. Nothing at all.

No GraphQL content type is required, no handshake, no framing, no custom
protocol. A GraphQL request is an ordinary HTTP POST whose body happens to be
JSON with a "query" string in it. To prove it, this file talks to a real
GraphQL endpoint with nothing but a TCP socket, typing every byte of the
request by hand, and then parses the response text by hand too.

This is optional. Nothing in levels 00-12 depends on it. It exists to answer
"but what is the client library actually doing for me?" once you are curious.
If you read REST/Foundation's level 13, this is the same exercise - and the
sameness IS the lesson.

You will learn
  - the exact bytes of a GraphQL request: request line, headers, blank line,
    JSON body - and that the body is the only part that knows about GraphQL
  - why Content-Length is mandatory: it is the only way the server knows where
    the body ends (the socket itself does not say)
  - how to split a raw response into status line / headers / body by hand
  - that {"data": ..., "errors": ...} is just text in that body, and the
    status line says 200 even when `errors` is populated

Run it   go run ./GraphQL/Foundation/golang/13_bonus_raw_http_over_tcp
*/
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strings"

	"github.com/graphql-go/graphql"
)

// ---- an ordinary GraphQL endpoint, exactly like level 11's -----------------
func buildSchema() graphql.Schema {
	query := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"greet": {
				Type: graphql.NewNonNull(graphql.String),
				Args: graphql.FieldConfigArgument{"name": {Type: graphql.NewNonNull(graphql.String)}},
				Resolve: func(p graphql.ResolveParams) (any, error) {
					return "hello, " + p.Args["name"].(string), nil
				},
			},
			"flaky": {
				Type:    graphql.String,
				Resolve: func(graphql.ResolveParams) (any, error) { return nil, errors.New("upstream is down") },
			},
		},
	})

	schema, err := graphql.NewSchema(graphql.SchemaConfig{Query: query})
	if err != nil {
		log.Fatal(err)
	}
	return schema
}

func graphqlHandler(schema graphql.Schema) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req struct {
			Query     string         `json:"query"`
			Variables map[string]any `json:"variables"`
		}
		body, _ := io.ReadAll(r.Body)
		json.Unmarshal(body, &req)
		result := graphql.Do(graphql.Params{
			Schema:         schema,
			RequestString:  req.Query,
			VariableValues: req.Variables,
		})
		payload, _ := json.Marshal(result)
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Content-Length", fmt.Sprint(len(payload)))
		w.Header().Set("Connection", "close")
		w.WriteHeader(http.StatusOK)
		w.Write(payload)
	}
}

// ---- the client, with no client library of any kind -----------------------

// rawGraphQLPost sends a GraphQL request as raw bytes over TCP and returns the
// raw response TEXT. This is the whole of what net/http does for you.
func rawGraphQLPost(address, query string, vars map[string]any, printRequest bool) string {
	// The body first, because we need its exact byte length for the header.
	body, _ := json.Marshal(map[string]any{"query": query, "variables": vars})

	// Every line ends with CRLF ("\r\n"), and a BLANK line separates the
	// headers from the body. Get either wrong and the server hangs waiting.
	requestText := fmt.Sprintf(
		"POST /graphql HTTP/1.1\r\n"+ // the request line: method, path, version
			"Host: %s\r\n"+ // mandatory in HTTP/1.1
			"Content-Type: application/json\r\n"+ // what the body is
			"Content-Length: %d\r\n"+ // HOW LONG the body is - not optional
			"Connection: close\r\n"+ // "answer, then hang up" - keeps this demo simple
			"\r\n", // the blank line: headers end here
		address, len(body)) + string(body) // ...and the body follows immediately

	if printRequest {
		fmt.Println("---- raw request bytes sent by the client ----")
		fmt.Println(requestText)
	}

	conn, err := net.Dial("tcp", address)
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()
	conn.Write([]byte(requestText))

	// Read until the server hangs up. We asked for Connection: close, so EOF
	// means "that was all of it".
	raw, err := io.ReadAll(conn)
	if err != nil {
		log.Fatal(err)
	}
	return string(raw)
}

// parseRawResponse splits a raw HTTP response into its three parts, by hand.
func parseRawResponse(responseText string) (statusLine, headerBlock, body string) {
	head, body, _ := strings.Cut(responseText, "\r\n\r\n") // the same blank line, in reverse
	statusLine, headerBlock, _ = strings.Cut(head, "\r\n")
	return statusLine, headerBlock, body
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	schema := buildSchema()

	// port 0 = "OS, pick me any free port".
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, graphqlHandler(schema))
	address := ln.Addr().String()

	responseText := rawGraphQLPost(address, `query Greet($n: String!) { greet(name: $n) }`,
		map[string]any{"n": "Ada"}, true)
	fmt.Println("---- raw response bytes received by the client ----")
	fmt.Println(responseText)

	statusLine, headerBlock, body := parseRawResponse(responseText)
	fmt.Printf("status line : %s\n", statusLine)
	fmt.Printf("headers     : %s\n", strings.Join(strings.Split(headerBlock, "\r\n"), " | "))
	fmt.Printf("body (text) : %s\n", body)

	must(statusLine == "HTTP/1.1 200 OK", "status line: "+statusLine)
	must(strings.Contains(headerBlock, fmt.Sprintf("Content-Length: %d", len(body))), "the length told the truth")

	// Only NOW does anything GraphQL-specific happen: we decode the body.
	var payload struct {
		Data   map[string]any   `json:"data"`
		Errors []map[string]any `json:"errors"`
	}
	must(json.Unmarshal([]byte(body), &payload) == nil, "the body is JSON")
	fmt.Printf("body (json) : data=%v errors=%v\n", payload.Data, payload.Errors)
	must(payload.Data["greet"] == "hello, Ada" && len(payload.Errors) == 0, "the answer")
	fmt.Println("   -> the socket, the headers, and HTTP itself never knew this was GraphQL")

	// Same wire, a field-level failure. The status line does not change.
	responseText = rawGraphQLPost(address, `{ greet(name: "Ada") flaky }`, nil, false)
	statusLine, _, body = parseRawResponse(responseText)
	fmt.Println("---- a request whose FIELD failed ----")
	fmt.Printf("status line : %s\n", statusLine)
	fmt.Printf("body (text) : %s\n", body)

	payload.Data, payload.Errors = nil, nil
	must(json.Unmarshal([]byte(body), &payload) == nil, "the body is JSON")
	must(statusLine == "HTTP/1.1 200 OK", "200, with errors in the body - level 06's rule, on the wire")
	must(payload.Data["greet"] == "hello, Ada" && payload.Data["flaky"] == nil, "partial data")
	must(len(payload.Errors) == 1 && payload.Errors[0]["message"] == "upstream is down", "the field error")
	fmt.Println("   -> HTTP said 'delivered successfully'. The message itself described a failure.")
	fmt.Println("      That is exactly why a GraphQL client must read the body, not the status.")

	fmt.Println("\nOK")
}
