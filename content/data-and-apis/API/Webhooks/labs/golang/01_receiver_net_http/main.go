/*
LAB 01 (basic) - A webhook receiver with net/http: verify, bound, acknowledge, hand off
========================================================================================
You will learn
  - the receiver's contract in four steps:
    1. read a BOUNDED raw body            (http.MaxBytesReader)
    2. verify the HMAC signature          (hmac.Equal - constant time)
    3. put the event on a queue           (do NOT process inline)
    4. answer 2xx immediately
  - why the RAW bytes must be verified (io.ReadAll(r.Body) once; never re-encode JSON)
  - the queue is BOUNDED: if the worker falls behind, reply 503 + Retry-After. The sender will retry
    later - that is back-pressure done right, better than accepting events you will lose in a crash
  - status code meanings the SENDER acts on:
    2xx  delivered       401/400  bad request (sender may retry/alert)
    5xx  retry later     429/503 + Retry-After  slow down
  - method routing with Go 1.22 ServeMux:  mux.HandleFunc("POST /webhooks/payments", ...)
  - graceful worker shutdown so queued events are finished before exit

Run it   go run ./Webhooks/labs/golang/01_receiver_net_http
*/
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

var secret = []byte("whsec_dev_secret")

func sign(body []byte) string {
	m := hmac.New(sha256.New, secret)
	m.Write(body)
	return hex.EncodeToString(m.Sum(nil))
}

type Event struct {
	ID   string          `json:"id"`
	Type string          `json:"type"`
	Data json.RawMessage `json:"data"`
}

type Receiver struct {
	queue     chan Event // BOUNDED hand-off to the worker
	processed atomic.Int64
	wg        sync.WaitGroup
	slow      time.Duration // makes the worker slow, to demonstrate back-pressure
}

func NewReceiver(queueSize int, workerDelay time.Duration) *Receiver {
	r := &Receiver{queue: make(chan Event, queueSize), slow: workerDelay}
	r.wg.Add(1)
	go r.worker()
	return r
}

func (rc *Receiver) worker() {
	defer rc.wg.Done()
	for ev := range rc.queue { // exits when the queue is closed AND drained
		time.Sleep(rc.slow)
		rc.processed.Add(1)
		_ = ev // ... real business logic here
	}
}

func (rc *Receiver) Close() { close(rc.queue); rc.wg.Wait() }

func (rc *Receiver) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("POST /webhooks/payments", func(w http.ResponseWriter, r *http.Request) {
		// 1. bounded raw body
		r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
		raw, err := io.ReadAll(r.Body)
		if err != nil {
			var tooBig *http.MaxBytesError
			if errors.As(err, &tooBig) {
				http.Error(w, "body too large", http.StatusRequestEntityTooLarge)
				return
			}
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}
		// 2. verify BEFORE parsing or acting
		got, err := hex.DecodeString(r.Header.Get("X-Signature"))
		m := hmac.New(sha256.New, secret)
		m.Write(raw)
		if err != nil || !hmac.Equal(got, m.Sum(nil)) { // constant-time compare on the raw MAC bytes
			http.Error(w, "invalid signature", http.StatusUnauthorized)
			return
		}
		// 3. parse
		var ev Event
		if err := json.Unmarshal(raw, &ev); err != nil || ev.ID == "" {
			http.Error(w, "invalid event", http.StatusBadRequest)
			return
		}
		// 4. hand off without blocking. A full queue means we cannot keep up: say so.
		select {
		case rc.queue <- ev:
			w.WriteHeader(http.StatusOK) // acknowledged: the sender can stop retrying
		default:
			w.Header().Set("Retry-After", "5")
			http.Error(w, "busy", http.StatusServiceUnavailable)
		}
	})
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) { fmt.Fprint(w, "ok") })
	return mux
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	rc := NewReceiver(4, 50*time.Millisecond) // tiny queue + slow worker on purpose
	srv := httptest.NewServer(rc.Handler())
	defer srv.Close()

	post := func(body string, sig string) *http.Response {
		req, _ := http.NewRequest("POST", srv.URL+"/webhooks/payments", strings.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		if sig != "" {
			req.Header.Set("X-Signature", sig)
		}
		res, err := http.DefaultClient.Do(req)
		must(err == nil, fmt.Sprint(err))
		res.Body.Close()
		return res
	}
	event := func(id string) string {
		return fmt.Sprintf(`{"id":%q,"type":"payment.succeeded","data":{"amount":4999}}`, id)
	}

	fmt.Println("== 1. signature checks ==")
	body := event("evt_1")
	res := post(body, sign([]byte(body)))
	fmt.Println("  valid signature        ->", res.StatusCode)
	must(res.StatusCode == 200, "valid")
	for name, sig := range map[string]string{
		"missing signature":    "",
		"garbage signature":    "zzzz",
		"signature of another": sign([]byte(event("evt_other"))),
	} {
		res = post(body, sig)
		fmt.Printf("  %-22s -> %d\n", name, res.StatusCode)
		must(res.StatusCode == 401, name)
	}
	tampered := strings.Replace(body, "4999", "1", 1)
	res = post(tampered, sign([]byte(body)))
	fmt.Println("  tampered body          ->", res.StatusCode)
	must(res.StatusCode == 401, "tampered")

	fmt.Println("\n== 2. malformed but correctly signed payload ==")
	bad := `{"not":"an event"}`
	res = post(bad, sign([]byte(bad)))
	fmt.Println("  valid signature, no id ->", res.StatusCode)
	must(res.StatusCode == 400, "validation after verification")

	fmt.Println("\n== 3. bounded body ==")
	huge := strings.Repeat("x", 2<<20)
	req, _ := http.NewRequest("POST", srv.URL+"/webhooks/payments", strings.NewReader(huge))
	req.Header.Set("X-Signature", sign([]byte(huge)))
	res, err := http.DefaultClient.Do(req)
	must(err == nil, "huge request completes with an HTTP error")
	res.Body.Close()
	fmt.Println("  2 MiB body             ->", res.StatusCode)
	must(res.StatusCode == 413, "size limit")

	fmt.Println("\n== 4. a burst larger than the queue: back-pressure instead of silent loss ==")
	codes := map[int]int{}
	var retryAfter string
	for i := 0; i < 12; i++ {
		b := event(fmt.Sprintf("evt_burst_%d", i))
		r := post(b, sign([]byte(b)))
		codes[r.StatusCode]++
		if r.StatusCode == 503 {
			retryAfter = r.Header.Get("Retry-After")
		}
	}
	fmt.Printf("  12 rapid events -> %v (503 carries Retry-After: %s)\n", codes, retryAfter)
	must(codes[200] >= 4 && codes[503] >= 1 && retryAfter == "5", "back-pressure")
	fmt.Println("  the sender's retry engine (Python lab 03) will redeliver the 503'd ones. Nothing was accepted-then-lost.")

	rc.Close() // graceful: drains the queue before returning
	fmt.Printf("\n== 5. graceful shutdown drained the queue: %d events processed ==\n", rc.processed.Load())
	must(rc.processed.Load() == int64(1+codes[200]), "every accepted event was processed")
	fmt.Println("\nOK")
}
