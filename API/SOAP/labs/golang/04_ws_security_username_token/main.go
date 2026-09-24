/*
LAB 04 (advanced) - WS-Security in Go: UsernameToken digest, Timestamp, nonce replay cache
===========================================================================================
You will learn

  - the security header, in Go structs:

    <wsse:Security>
    <wsu:Timestamp><wsu:Created/><wsu:Expires/></wsu:Timestamp>      <- message lifetime
    <wsse:UsernameToken>
    <wsse:Username/><wsse:Password Type="...#PasswordDigest"/>       Base64(SHA1(nonce + created + password))
    <wsse:Nonce/><wsu:Created/>
    </wsse:UsernameToken>
    </wsse:Security>

  - a cross-language KNOWN-ANSWER TEST: the digest for fixed inputs was produced by the Python track
    (lab 04, whose implementation interoperates with the zeep library) and must match here byte for byte

  - verification order that leaks nothing:
    structure -> Timestamp (expired? too far in the future?) -> token freshness -> digest (constant
    time, and the SAME work for unknown users) -> nonce cache LAST (only burn nonces of valid tokens)

  - clock skew: tolerate a couple of minutes either way, not hours

  - the nonce cache: entries live for exactly the acceptance window; never evict early or a nonce
    becomes replayable again (bound memory by rate-limiting instead)

  - the HONEST LIMIT (demonstrated!): UsernameToken authenticates the sender but does NOT protect the
    body. A man-in-the-middle can swap the body and the token is still valid. The fixes are TLS
    (always) and, where messages cross intermediaries, XML Signature over Body + Timestamp.

Run it   go run ./SOAP/labs/golang/04_ws_security_username_token
*/
package main

import (
	"crypto/rand"
	"crypto/sha1" //nolint:gosec // SHA-1 is mandated by the UsernameToken PasswordDigest profile
	"crypto/subtle"
	"encoding/base64"
	"encoding/xml"
	"errors"
	"fmt"
	"strings"
	"sync"
	"time"
)

const (
	nsSOAP     = "http://schemas.xmlsoap.org/soap/envelope/"
	nsWSSE     = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
	nsWSU      = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
	typeDigest = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest"
	typeText   = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText"
)

// ------------------------------------------------------------------ structs ---
type Envelope struct {
	XMLName xml.Name `xml:"http://schemas.xmlsoap.org/soap/envelope/ Envelope"`
	Header  struct {
		Security *Security `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd Security"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Header"`
	Body struct {
		Inner string `xml:",innerxml"`
	} `xml:"http://schemas.xmlsoap.org/soap/envelope/ Body"`
}

type Security struct {
	Timestamp *struct {
		Created string `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd Created"`
		Expires string `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd Expires"`
	} `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd Timestamp"`
	Token *struct {
		Username string `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd Username"`
		Password struct {
			Type  string `xml:"Type,attr"`
			Value string `xml:",chardata"`
		} `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd Password"`
		Nonce   string `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd Nonce"`
		Created string `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd Created"`
	} `xml:"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd UsernameToken"`
}

// ------------------------------------------------------------------- digest ---
func digest(nonce []byte, created, password string) string {
	h := sha1.New()
	h.Write(nonce)
	h.Write([]byte(created))
	h.Write([]byte(password))
	return base64.StdEncoding.EncodeToString(h.Sum(nil))
}

const tsFormat = "2006-01-02T15:04:05Z"

// BuildRequest is the CLIENT side: produce a secured envelope.
func BuildRequest(user, password string, now time.Time, nonce []byte, bodyInner string) string {
	if nonce == nil {
		nonce = make([]byte, 16)
		rand.Read(nonce)
	}
	created := now.UTC().Format(tsFormat)
	expires := now.Add(5 * time.Minute).UTC().Format(tsFormat)
	return fmt.Sprintf(`<soap:Envelope xmlns:soap=%q xmlns:wsse=%q xmlns:wsu=%q><soap:Header><wsse:Security>`+
		`<wsu:Timestamp><wsu:Created>%s</wsu:Created><wsu:Expires>%s</wsu:Expires></wsu:Timestamp>`+
		`<wsse:UsernameToken><wsse:Username>%s</wsse:Username><wsse:Password Type=%q>%s</wsse:Password>`+
		`<wsse:Nonce>%s</wsse:Nonce><wsu:Created>%s</wsu:Created></wsse:UsernameToken></wsse:Security></soap:Header>`+
		`<soap:Body>%s</soap:Body></soap:Envelope>`,
		nsSOAP, nsWSSE, nsWSU, created, expires, user, typeDigest, digest(nonce, created, password),
		base64.StdEncoding.EncodeToString(nonce), created, bodyInner)
}

// ----------------------------------------------------------------- verifier ---
var ErrAuth = errors.New("the security token could not be authenticated") // the ONLY thing clients ever see

type Verifier struct {
	Users  map[string]string
	Window time.Duration // freshness window for token and timestamp
	Skew   time.Duration // tolerated clock difference
	mu     sync.Mutex
	nonces map[string]time.Time
}

func NewVerifier(users map[string]string) *Verifier {
	return &Verifier{Users: users, Window: 5 * time.Minute, Skew: 2 * time.Minute, nonces: map[string]time.Time{}}
}

// Verify returns the authenticated user, or ErrAuth. `reason` is for the SERVER LOG only.
func (v *Verifier) Verify(raw string, now time.Time) (user string, reason string, err error) {
	var env Envelope
	if e := xml.Unmarshal([]byte(raw), &env); e != nil || env.Header.Security == nil || env.Header.Security.Token == nil {
		return "", "missing or malformed security header", ErrAuth
	}
	sec, tok := env.Header.Security, env.Header.Security.Token
	if tok.Password.Type != typeDigest {
		return "", "PasswordText rejected by policy", ErrAuth
	}
	created, e1 := time.Parse(tsFormat, tok.Created)
	nonce, e2 := base64.StdEncoding.DecodeString(tok.Nonce)
	if e1 != nil || e2 != nil || len(nonce) < 8 {
		return "", "malformed created/nonce", ErrAuth
	}
	// 1. message lifetime (Timestamp), when present
	if sec.Timestamp != nil {
		exp, e := time.Parse(tsFormat, sec.Timestamp.Expires)
		if e != nil || now.After(exp.Add(v.Skew)) {
			return "", "Timestamp expired", ErrAuth
		}
	}
	// 2. token freshness, in BOTH directions
	if d := now.Sub(created); d > v.Window || d < -v.Skew {
		return "", fmt.Sprintf("token created %s away from now", d.Round(time.Second)), ErrAuth
	}
	// 3. digest, constant time, same work for unknown users
	password, known := v.Users[tok.Username]
	expected := digest(nonce, tok.Created, password) // password "" for unknown users: still computes
	if subtle.ConstantTimeCompare([]byte(expected), []byte(strings.TrimSpace(tok.Password.Value))) != 1 || !known {
		return "", "bad credentials", ErrAuth
	}
	// 4. nonce cache LAST: only valid tokens may consume a nonce
	v.mu.Lock()
	defer v.mu.Unlock()
	for n, t := range v.nonces { // sweep entries older than the window (they can no longer be replayed anyway)
		if now.Sub(t) > v.Window+v.Skew {
			delete(v.nonces, n)
		}
	}
	key := tok.Username + "|" + tok.Nonce
	if _, seen := v.nonces[key]; seen {
		return "", "nonce reuse (replay)", ErrAuth
	}
	v.nonces[key] = now
	return tok.Username, "", nil
}

func must(ok bool, what string) {
	if !ok {
		panic("FAILED: " + what)
	}
}

func main() {
	users := map[string]string{"alice": "s3cret-alice", "bob": "s3cret-bob"}
	v := NewVerifier(users)
	now := time.Date(2026, 9, 21, 10, 30, 0, 0, time.UTC)
	body := `<GetBalance xmlns="http://bank.example.com/ws"><accountId>ACC-1001</accountId></GetBalance>`

	fmt.Println("== 1. cross-language known-answer test ==")
	fixedNonce := make([]byte, 16)
	for i := range fixedNonce {
		fixedNonce[i] = byte(i)
	}
	got := digest(fixedNonce, "2026-09-21T10:30:00Z", "s3cret-alice")
	fmt.Println("  nonce=AAECAwQFBgcICQoLDA0ODw== created=2026-09-21T10:30:00Z password=s3cret-alice")
	fmt.Println("  expected (produced by the Python track, verified there against zeep): tyuDneBfRWH8T5kRpTol5138qow=")
	fmt.Println("  computed here                                                     :", got)
	must(got == "tyuDneBfRWH8T5kRpTol5138qow=", "digest interoperates with the Python/zeep implementation")

	type tc struct {
		name string
		msg  func() string
		ok   bool
	}
	var replayable string
	cases := []tc{
		{"valid message", func() string { replayable = BuildRequest("alice", "s3cret-alice", now, nil, body); return replayable }, true},
		{"the SAME bytes again (replay)", func() string { return replayable }, false},
		{"wrong password", func() string { return BuildRequest("alice", "wrong", now, nil, body) }, false},
		{"unknown user", func() string { return BuildRequest("mallory", "x", now, nil, body) }, false},
		{"token from 1 hour ago", func() string { return BuildRequest("bob", "s3cret-bob", now.Add(-time.Hour), nil, body) }, false},
		{"token from 1 hour in the future", func() string { return BuildRequest("bob", "s3cret-bob", now.Add(time.Hour), nil, body) }, false},
		{"clock skew of +90s (tolerated)", func() string { return BuildRequest("bob", "s3cret-bob", now.Add(90*time.Second), nil, body) }, true},
		{"clock skew of +5min (rejected)", func() string { return BuildRequest("bob", "s3cret-bob", now.Add(5*time.Minute), nil, body) }, false},
		{"no security header at all", func() string {
			return `<soap:Envelope xmlns:soap="` + nsSOAP + `"><soap:Body>` + body + `</soap:Body></soap:Envelope>`
		}, false},
		{"PasswordText instead of digest", func() string {
			return strings.Replace(BuildRequest("alice", "s3cret-alice", now, nil, body), typeDigest, typeText, 1)
		}, false},
	}
	fmt.Println("\n== 2. verification matrix ==")
	fmt.Printf("  %-34s %-9s %s\n", "case", "result", "server-side reason (never sent to the client)")
	for _, c := range cases {
		user, reason, err := v.Verify(c.msg(), now)
		res := "REJECTED"
		if err == nil {
			res = "accepted"
		}
		fmt.Printf("  %-34s %-9s %s\n", c.name, res, orDash(reason, user))
		must((err == nil) == c.ok, c.name)
		if err != nil {
			must(err.Error() == "the security token could not be authenticated", "uniform client-facing error")
		}
	}
	fmt.Println("  every rejection produced the IDENTICAL client-facing message: an attacker learns nothing")

	fmt.Println("\n== 3. the honest limit: the token does not protect the BODY ==")
	original := BuildRequest("alice", "s3cret-alice", now, nil, body)
	tampered := strings.Replace(original, "ACC-1001", "ACC-9999", 1)
	// A man-in-the-middle intercepts the ORIGINAL (never forwarded, so its nonce is unused), edits the body, forwards it:
	user, reason, err := v.Verify(tampered, now)
	fmt.Printf("  body changed ACC-1001 -> ACC-9999 in transit: err=%v user=%q reason=%q\n", err, user, reason)
	must(err == nil, "UsernameToken alone does not detect body tampering")
	fmt.Println("  => authentication proved WHO built the token, not WHAT the body says. Defences:")
	fmt.Println("     1. TLS on every hop (removes the man-in-the-middle),")
	fmt.Println("     2. XML Signature (ds:Signature) over the Body AND the Timestamp when messages cross intermediaries.")

	fmt.Println("\n== 4. nonce cache hygiene ==")
	fmt.Printf("  nonces remembered: %d\n", len(v.nonces))
	later := now.Add(20 * time.Minute)
	v.Verify(BuildRequest("bob", "s3cret-bob", later, nil, body), later) // triggers the sweep
	fmt.Printf("  after 20 minutes and one more request: %d (old entries swept; they could not be replayed anyway)\n", len(v.nonces))
	must(len(v.nonces) == 1, "sweep")
	fmt.Println("  never evict a nonce BEFORE the window ends (e.g. an LRU cap): it would become replayable. Bound memory")
	fmt.Println("  by rate-limiting authentication attempts per client instead.")
	fmt.Println("\nOK")
}

func orDash(reason, user string) string {
	if reason == "" {
		return "authenticated as " + user
	}
	return reason
}
