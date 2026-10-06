/*
FOUNDATION LEVEL 06 - The full status-code vocabulary, and CRUD-to-verb mapping
==================================================================================
Levels 00-06 used 200/201/400/404 as they came up naturally. This level is the
deliberate, full picture: which HTTP verb means which CRUD action, and which
status code means what, on purpose, all in one place, on ONE resource.

You will learn
  - POST=Create, GET=Read, PUT=Replace(whole thing), DELETE=Remove
  - 201 Created should carry a Location header pointing at the new resource
  - 204 No Content means "it worked, there is nothing to send back"
  - DELETE is idempotent BY DESIGN: deleting something twice is not an error,
    the resource is simply gone both times
  - 405 Method Not Allowed should carry an Allow header listing what IS allowed

Run it   go run ./REST/Foundation/golang/06_status_codes_and_crud_verbs
*/
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strconv"
	"strings"
)

type Note struct {
	ID   int    `json:"id"`
	Text string `json:"text"`
}

var (
	notes  = map[int]Note{}
	nextID = 1
)

func sendJSON(w http.ResponseWriter, status int, payload any, headers map[string]string) {
	for k, v := range headers {
		w.Header().Set(k, v)
	}
	if payload != nil {
		w.Header().Set("Content-Type", "application/json")
	}
	w.WriteHeader(status)
	if payload != nil {
		json.NewEncoder(w).Encode(payload)
	}
}

func noteID(path string) (int, bool) {
	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) != 2 || parts[0] != "notes" {
		return 0, false
	}
	id, err := strconv.Atoi(parts[1])
	return id, err == nil
}

func handler(w http.ResponseWriter, r *http.Request) {
	id, hasID := noteID(r.URL.Path)

	switch {
	case r.Method == http.MethodGet && r.URL.Path == "/notes":
		list := make([]Note, 0, len(notes))
		for _, n := range notes {
			list = append(list, n)
		}
		sendJSON(w, http.StatusOK, list, nil)

	case r.Method == http.MethodGet && hasID:
		if n, ok := notes[id]; ok {
			sendJSON(w, http.StatusOK, n, nil)
		} else {
			sendJSON(w, http.StatusNotFound, map[string]string{"error": "note not found"}, nil)
		}

	case r.Method == http.MethodPost && r.URL.Path == "/notes":
		var body struct {
			Text string `json:"text"`
		}
		json.NewDecoder(r.Body).Decode(&body)
		n := Note{ID: nextID, Text: body.Text}
		notes[nextID] = n
		nextID++
		// 201 + Location: the client did not choose the id, so tell it where the new thing lives.
		sendJSON(w, http.StatusCreated, n, map[string]string{"Location": fmt.Sprintf("/notes/%d", n.ID)})

	case r.Method == http.MethodPost:
		sendJSON(w, http.StatusMethodNotAllowed, nil, map[string]string{"Allow": "GET"})

	case r.Method == http.MethodPut && hasID:
		if _, ok := notes[id]; !ok {
			sendJSON(w, http.StatusNotFound, map[string]string{"error": "note not found"}, nil)
			return
		}
		var body struct {
			Text string `json:"text"`
		}
		json.NewDecoder(r.Body).Decode(&body)
		notes[id] = Note{ID: id, Text: body.Text} // PUT REPLACES the whole thing
		sendJSON(w, http.StatusOK, notes[id], nil)

	case r.Method == http.MethodDelete && hasID:
		delete(notes, id) // missing key is fine: idempotent by design
		sendJSON(w, http.StatusNoContent, nil, nil)

	default:
		sendJSON(w, http.StatusNotFound, map[string]string{"error": "not found"}, nil)
	}
}

func call(method, base, path, body string) (int, http.Header, string) {
	var reqBody io.Reader
	if body != "" {
		reqBody = strings.NewReader(body)
	}
	req, _ := http.NewRequest(method, base+path, reqBody)
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Fatal(err)
	}
	defer res.Body.Close()
	b, _ := io.ReadAll(res.Body)
	return res.StatusCode, res.Header, string(b)
}

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go http.Serve(ln, http.HandlerFunc(handler))
	base := "http://" + ln.Addr().String()

	s, h, b := call("POST", base, "/notes", `{"text": "learn REST"}`)
	fmt.Printf("POST /notes         -> %d Location=%s %s", s, h.Get("Location"), b)
	if s != 201 || h.Get("Location") != "/notes/1" {
		panic("FAILED")
	}

	s, _, b = call("PUT", base, "/notes/1", `{"text": "learn REST, for real"}`)
	fmt.Printf("PUT  /notes/1       -> %d %s", s, b)
	if s != 200 {
		panic("FAILED")
	}

	s, h, _ = call("POST", base, "/notes/1", `{"text": "x"}`)
	fmt.Printf("POST /notes/1       -> %d Allow=%s   (wrong verb for this path)\n", s, h.Get("Allow"))
	if s != 405 {
		panic("FAILED")
	}

	s1, _, _ := call("DELETE", base, "/notes/1", "")
	s2, _, _ := call("DELETE", base, "/notes/1", "")
	fmt.Printf("DELETE /notes/1 x2  -> %d, %d   (idempotent: deleting twice is not an error)\n", s1, s2)
	if s1 != 204 || s2 != 204 {
		panic("FAILED")
	}
	fmt.Println("OK")
}
