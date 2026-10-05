/*
FOUNDATION LEVEL 02 - Speaking JSON instead of plain text
============================================================
Real APIs exchange structured data, not plain sentences. JSON is just a text
format (plain text, the way HTTP itself is plain text) with its own tiny grammar for numbers,
strings, lists and objects. Go's encoding/json converts between that text and
native struct/map values.

You will learn
  - json.Marshal(v) -> []byte of JSON text ; json.Unmarshal(bytes, &v) -> back
  - struct field tags (`json:"name"`) control the exact key names on the wire
  - Content-Type: application/json tells the CLIENT how to interpret the
    bytes - the server does not enforce anything by setting this header

Run it   go run ./REST/Foundation/golang/02_json_in_and_out
*/
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
)

type Profile struct {
	Name      string   `json:"name"`
	Languages []string `json:"languages"`
}

func handler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/profile" {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(map[string]string{"error": "not found"})
		return
	}
	profile := Profile{Name: "Ada", Languages: []string{"Go", "Python"}}
	body, _ := json.Marshal(profile)
	w.Header().Set("Content-Type", "application/json")
	w.Write(body)
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(handler))
	base := "http://" + ln.Addr().String()

	res, err := http.Get(base + "/profile")
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	rawBytes, _ := io.ReadAll(res.Body)
	contentType := res.Header.Get("Content-Type")

	fmt.Printf("raw bytes on the wire : %s\n", rawBytes)
	fmt.Printf("Content-Type header   : %s\n", contentType)

	// This is the whole point of level 02: turn wire-format text back into a
	// real Go value you can access by field, exactly like any other struct.
	var parsed Profile
	if err := json.Unmarshal(rawBytes, &parsed); err != nil {
		log.Fatal(err)
	}
	fmt.Printf("parsed Go struct       : %+v\n", parsed)

	if contentType != "application/json" {
		panic("FAILED: wrong content type")
	}
	if parsed.Name != "Ada" || parsed.Languages[0] != "Go" {
		panic("FAILED: wrong parsed value")
	}
	fmt.Println("OK")
}
