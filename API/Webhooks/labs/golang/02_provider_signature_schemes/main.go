/*
LAB 02 (basic) - Verifying real-world providers: Stripe, GitHub and Slack signature schemes
===========================================================================================
Every provider signs differently. They are all "HMAC-SHA256 of something with a shared secret", but
the details - WHAT is signed, how the signature is ENCODED, how REPLAYS are prevented - differ:

	provider   header                      signed content                      replay protection
	---------  --------------------------  ----------------------------------  ----------------------
	GitHub     X-Hub-Signature-256         raw body                            none (dedupe on X-GitHub-Delivery)
	           "sha256=<hex>"
	Stripe     Stripe-Signature            "<timestamp>.<raw body>"            timestamp tolerance (5 min)
	           "t=<ts>,v1=<hex>[,v1=...]"
	Slack      X-Slack-Signature           "v0:<timestamp>:<raw body>"         timestamp tolerance (5 min)
	           "v0=<hex>" + X-Slack-Request-Timestamp

You will learn
  - to implement all three as small pure functions (easy to test, no HTTP needed)
  - a known-answer test straight from GitHub's documentation
  - table-driven tests for the attacks each scheme must survive: tampering, wrong secret, stale
    timestamp, future timestamp, missing header, wrong prefix, malformed hex
  - the generic verify shape:  parse header -> check freshness -> recompute -> hmac.Equal
  - why comparing HEX STRINGS with == is wrong and hmac.Equal on decoded bytes (or the raw MAC) is right
  - Stripe's rotation feature: several v1= values, accept if ANY matches

Note: GitHub publishes a test vector (used below). The Stripe and Slack functions follow their public
documentation and are tested against our own signers; in production prefer the vendor's official
SDK verifier (stripe.webhook.ConstructEvent, Slack's SDK) and keep this lab as the "how it works" view.

Run it   go run ./Webhooks/labs/golang/02_provider_signature_schemes
*/
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"
)

const tolerance = 5 * time.Minute

func mac(secret string, parts ...string) []byte {
	m := hmac.New(sha256.New, []byte(secret))
	for _, p := range parts {
		m.Write([]byte(p))
	}
	return m.Sum(nil)
}

// equalHex compares a hex signature from a header against the expected MAC in constant time.
func equalHex(gotHex string, want []byte) bool {
	got, err := hex.DecodeString(gotHex) // malformed hex => false, never a panic
	return err == nil && hmac.Equal(got, want)
}

var (
	ErrMissing = errors.New("missing or malformed signature header")
	ErrStale   = errors.New("timestamp outside tolerance")
	ErrNoMatch = errors.New("signature does not match")
)

// ------------------------------------------------------------------ GitHub ---
func VerifyGitHub(secret string, body []byte, header string) error {
	hexSig, ok := strings.CutPrefix(header, "sha256=")
	if !ok {
		return ErrMissing // (the older X-Hub-Signature with sha1= is deprecated; do not accept it)
	}
	if !equalHex(hexSig, mac(secret, string(body))) {
		return ErrNoMatch
	}
	return nil
}

// ------------------------------------------------------------------ Stripe ---
func VerifyStripe(secret string, body []byte, header string, now time.Time) error {
	var ts int64
	var sigs []string
	for _, part := range strings.Split(header, ",") {
		k, v, _ := strings.Cut(strings.TrimSpace(part), "=")
		switch k {
		case "t":
			ts, _ = strconv.ParseInt(v, 10, 64)
		case "v1": // there can be several v1= entries during secret rotation
			sigs = append(sigs, v)
		}
	}
	if ts == 0 || len(sigs) == 0 {
		return ErrMissing
	}
	if now.Sub(time.Unix(ts, 0)).Abs() > tolerance {
		return ErrStale
	}
	want := mac(secret, strconv.FormatInt(ts, 10), ".", string(body)) // "<t>.<body>"
	for _, s := range sigs {
		if equalHex(s, want) {
			return nil
		}
	}
	return ErrNoMatch
}

// ------------------------------------------------------------------- Slack ---
func VerifySlack(secret string, body []byte, tsHeader, sigHeader string, now time.Time) error {
	ts, err := strconv.ParseInt(tsHeader, 10, 64)
	hexSig, ok := strings.CutPrefix(sigHeader, "v0=")
	if err != nil || !ok {
		return ErrMissing
	}
	if now.Sub(time.Unix(ts, 0)).Abs() > tolerance {
		return ErrStale
	}
	if !equalHex(hexSig, mac(secret, "v0:", tsHeader, ":", string(body))) { // "v0:<ts>:<body>"
		return ErrNoMatch
	}
	return nil
}

// ------------------------------------------------------- test signers (the SENDER side) ---
func signGitHub(secret string, body []byte) string {
	return "sha256=" + hex.EncodeToString(mac(secret, string(body)))
}
func signStripe(secret string, body []byte, ts time.Time) string {
	t := strconv.FormatInt(ts.Unix(), 10)
	return "t=" + t + ",v1=" + hex.EncodeToString(mac(secret, t, ".", string(body)))
}
func signSlack(secret string, body []byte, ts time.Time) (string, string) {
	t := strconv.FormatInt(ts.Unix(), 10)
	return t, "v0=" + hex.EncodeToString(mac(secret, "v0:", t, ":", string(body)))
}

type testCase struct {
	name string
	want error // nil = must be accepted
	run  func() error
}

func main() {
	now := time.Unix(1_800_000_000, 0)
	secret, body := "topsecret", []byte(`{"action":"opened","number":42}`)

	fmt.Println("== 1. known-answer test from GitHub's documentation ==")
	docSecret, docBody := "It's a Secret to Everybody", []byte("Hello, World!")
	docHeader := "sha256=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e17"
	fmt.Println("  secret \"It's a Secret to Everybody\", body \"Hello, World!\"")
	fmt.Println("  expected:", docHeader)
	fmt.Println("  computed:", signGitHub(docSecret, docBody))
	if VerifyGitHub(docSecret, docBody, docHeader) != nil || signGitHub(docSecret, docBody) != docHeader {
		panic("FAILED: GitHub test vector")
	}
	fmt.Println("  -> matches the published vector")

	tsOld, tsNew := now.Add(-10*time.Minute), now.Add(-30*time.Second)
	slackTS, slackSig := signSlack(secret, body, tsNew)
	oldSlackTS, oldSlackSig := signSlack(secret, body, tsOld)
	stripeGood := signStripe(secret, body, tsNew)
	otherKey := signStripe("newsecret", body, tsNew)
	rotation := stripeGood + "," + strings.SplitN(otherKey, ",", 2)[1] // two v1= values (old and new secret)

	cases := []testCase{
		{"github: valid", nil, func() error { return VerifyGitHub(secret, body, signGitHub(secret, body)) }},
		{"github: tampered body", ErrNoMatch, func() error {
			return VerifyGitHub(secret, append([]byte{}, body[:len(body)-1]...), signGitHub(secret, body))
		}},
		{"github: wrong secret", ErrNoMatch, func() error { return VerifyGitHub("wrong", body, signGitHub(secret, body)) }},
		{"github: sha1 header rejected", ErrMissing, func() error { return VerifyGitHub(secret, body, "sha1=abcdef") }},
		{"github: empty header", ErrMissing, func() error { return VerifyGitHub(secret, body, "") }},
		{"github: non-hex garbage", ErrNoMatch, func() error { return VerifyGitHub(secret, body, "sha256=not-hex!!") }},

		{"stripe: valid", nil, func() error { return VerifyStripe(secret, body, stripeGood, now) }},
		{"stripe: tampered body", ErrNoMatch, func() error { return VerifyStripe(secret, []byte(`{"action":"closed"}`), stripeGood, now) }},
		{"stripe: 10 minutes old (replay)", ErrStale, func() error { return VerifyStripe(secret, body, signStripe(secret, body, tsOld), now) }},
		{"stripe: timestamp in the future", ErrStale, func() error { return VerifyStripe(secret, body, signStripe(secret, body, now.Add(time.Hour)), now) }},
		{"stripe: timestamp edited, old sig", ErrNoMatch, func() error {
			return VerifyStripe(secret, body, "t="+strconv.FormatInt(now.Unix(), 10)+","+strings.SplitN(signStripe(secret, body, tsOld), ",", 2)[1], now)
		}},
		{"stripe: two v1= (rotation), old secret matches", nil, func() error { return VerifyStripe(secret, body, rotation, now) }},
		{"stripe: two v1= (rotation), new secret matches", nil, func() error { return VerifyStripe("newsecret", body, rotation, now) }},
		{"stripe: header without v1", ErrMissing, func() error { return VerifyStripe(secret, body, "t=123", now) }},

		{"slack: valid", nil, func() error { return VerifySlack(secret, body, slackTS, slackSig, now) }},
		{"slack: 10 minutes old", ErrStale, func() error { return VerifySlack(secret, body, oldSlackTS, oldSlackSig, now) }},
		{"slack: wrong prefix v1=", ErrMissing, func() error { return VerifySlack(secret, body, slackTS, "v1=abc", now) }},
		{"slack: timestamp swapped, sig kept", ErrNoMatch, func() error { return VerifySlack(secret, body, strconv.FormatInt(now.Unix(), 10), oldSlackSig, now) }},
	}

	fmt.Println("\n== 2. table-driven attack tests ==")
	for _, c := range cases {
		got := c.run()
		verdict := "accepted"
		if got != nil {
			verdict = "rejected: " + got.Error()
		}
		fmt.Printf("  %-48s %s\n", c.name, verdict)
		if !errors.Is(got, c.want) && !(got == nil && c.want == nil) {
			panic(fmt.Sprintf("FAILED %s: got %v, want %v", c.name, got, c.want))
		}
	}

	fmt.Println("\n== 3. why == on hex strings is the wrong comparison ==")
	fmt.Println("  string == returns as soon as one byte differs, so response TIME leaks how many leading")
	fmt.Println("  characters of a forged signature were right. hmac.Equal takes the same time regardless.")
	fmt.Println("  Also normalise: hex.DecodeString accepts upper and lower case; a string compare would not.")
	up := strings.ToUpper(strings.TrimPrefix(signGitHub(secret, body), "sha256="))
	if VerifyGitHub(secret, body, "sha256="+up) != nil {
		panic("FAILED: uppercase hex should verify via byte comparison")
	}
	fmt.Println("  uppercase hex signature verified correctly through decoding")
	fmt.Println("\nOK")
}
