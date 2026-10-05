/*
LAB 08 (advanced) - Contract testing, provider side: verification, a broker, "can I deploy?"
===========================================================================================
You will learn

  - the PROVIDER half of consumer-driven contracts (Python lab 06 builds the consumer half):
    fetch every consumer's pact, put the provider into each "provider state", replay each
    request against the REAL running provider, match the response with the pact's rules

  - the BROKER: the service that stores pacts and verification results, and knows which
    version of every app is deployed where. Real ones: Pact Broker (open source), PactFlow.

  - can-i-deploy: "may orders-api v2 go to production?" is answered by the MATRIX of
    (consumer version x provider version) verification results, restricted to what is
    actually deployed in production right now

  - expand then contract: why renaming a field takes THREE deploys, and the deploy ORDER
    the broker forces on you when a consumer starts needing a new field

  - small real details: provider-state setup over HTTP (only in test builds), identical pact
    content keeps its verification results (content hash), and a pact nobody verified yet
    is a "no", not a "yes"

    checkout-web ----publish pact----> BROKER <----verification results---- orders-api CI
    mobile-app   ----publish pact---->   |                                      |
    +---- can-i-deploy? (matrix + env) ----+
    |
    record-deployment after each release

Run it   go run ./REST/labs/golang/08_provider_verification_and_can_i_deploy
*/
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"regexp"
	"sort"
	"strings"
	"sync"
)

// ============================================================ the pact format ===
// The same Pact v3 layout the Python lab writes.
type Pact struct {
	Consumer     struct{ Name string } `json:"consumer"`
	Provider     struct{ Name string } `json:"provider"`
	Interactions []Interaction         `json:"interactions"`
}

type Interaction struct {
	Description    string `json:"description"`
	ProviderStates []struct {
		Name string `json:"name"`
	} `json:"providerStates"`
	Request struct {
		Method string `json:"method"`
		Path   string `json:"path"`
		Body   any    `json:"body,omitempty"`
	} `json:"request"`
	Response struct {
		Status        int                       `json:"status"`
		Body          any                       `json:"body"`
		MatchingRules map[string]map[string]any `json:"matchingRules"`
	} `json:"response"`
}

// pactJSON builds a pact for GET /orders/42 that reads the given fields (all type-matched).
func pactJSON(consumer string, fields ...string) []byte {
	body, rules := map[string]any{"id": 42}, map[string]any{"$.id": typeRule()}
	examples := map[string]any{"total_cents": 1999, "currency": "USD", "status": "PAID",
		"total": map[string]any{"amount": 1999, "currency": "USD"}}
	for _, f := range fields {
		body[f] = examples[f]
		rules["$."+f] = typeRule()
		// A rule covers ONE path. For an object, give each child its own type rule, or the
		// matcher would compare the example values (1999) literally with the provider's (4598).
		if obj, ok := examples[f].(map[string]any); ok {
			for k := range obj {
				rules["$."+f+"."+k] = typeRule()
			}
		}
	}
	p := map[string]any{
		"consumer": map[string]string{"name": consumer}, "provider": map[string]string{"name": "orders-api"},
		"interactions": []any{map[string]any{
			"description":    "a request for order 42",
			"providerStates": []any{map[string]string{"name": "order 42 exists"}},
			"request":        map[string]any{"method": "GET", "path": "/orders/42"},
			"response":       map[string]any{"status": 200, "body": body, "matchingRules": map[string]any{"body": rules}},
		}},
		"metadata": map[string]any{"pactSpecification": map[string]string{"version": "3.0.0"}},
	}
	b, _ := json.Marshal(p)
	return b
}

func typeRule() map[string]any {
	return map[string]any{"matchers": []any{map[string]any{"match": "type"}}}
}

// ================================================================ matching ===
var indexRe = regexp.MustCompile(`\[\d+\]`)

func kind(v any) string {
	switch v.(type) {
	case nil:
		return "null"
	case bool:
		return "boolean"
	case float64:
		return "number"
	case string:
		return "string"
	case []any:
		return "array"
	default:
		return "object"
	}
}

// match: extra fields in the actual response are allowed; missing ones and rule violations are not.
func match(expected, actual any, path string, rules map[string]any, errs *[]string) {
	var rule map[string]any
	if r, ok := rules[indexRe.ReplaceAllString(path, "[*]")].(map[string]any); ok {
		rule = r["matchers"].([]any)[0].(map[string]any)
	}
	if rule != nil && rule["match"] == "regex" {
		s, ok := actual.(string)
		if !ok || !regexp.MustCompile("^(?:"+rule["regex"].(string)+")$").MatchString(s) {
			*errs = append(*errs, fmt.Sprintf("%s: %v does not match /%v/", path, actual, rule["regex"]))
		}
		return
	}
	switch e := expected.(type) {
	case map[string]any:
		a, ok := actual.(map[string]any)
		if !ok {
			*errs = append(*errs, fmt.Sprintf("%s: expected an object, got %v", path, kind(actual)))
			return
		}
		keys := make([]string, 0, len(e))
		for k := range e {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			if av, present := a[k]; !present {
				*errs = append(*errs, fmt.Sprintf("%s.%s: missing", path, k))
			} else {
				match(e[k], av, path+"."+k, rules, errs)
			}
		}
	default:
		if rule != nil && rule["match"] == "type" {
			if kind(expected) != kind(actual) {
				*errs = append(*errs, fmt.Sprintf("%s: expected a %s, got %s", path, kind(expected), kind(actual)))
			}
		} else if fmt.Sprint(expected) != fmt.Sprint(actual) {
			*errs = append(*errs, fmt.Sprintf("%s: expected %v, got %v", path, expected, actual))
		}
	}
}

// ================================================================== broker ===
type Broker struct {
	mu            sync.Mutex
	pacts         map[string][]byte            // "consumer@version" -> pact JSON (provider is orders-api here)
	verifications map[string]bool              // "contentHash|providerVersion" -> success
	deployed      map[string]map[string]string // env -> pacticipant -> version
}

func contentHash(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:6]) }

func NewBroker() http.Handler {
	b := &Broker{pacts: map[string][]byte{}, verifications: map[string]bool{},
		deployed: map[string]map[string]string{"production": {}}}
	mux := http.NewServeMux()

	mux.HandleFunc("PUT /pacts/provider/orders-api/consumer/{c}/version/{v}", func(w http.ResponseWriter, r *http.Request) {
		var buf bytes.Buffer
		buf.ReadFrom(r.Body)
		b.mu.Lock()
		b.pacts[r.PathValue("c")+"@"+r.PathValue("v")] = buf.Bytes()
		b.mu.Unlock()
		w.WriteHeader(http.StatusCreated)
	})
	// The pacts a provider build must verify: the consumer versions deployed to each environment,
	// plus any explicitly requested one (real brokers call these "consumer version selectors").
	mux.HandleFunc("GET /pacts/provider/orders-api/for-verification", func(w http.ResponseWriter, r *http.Request) {
		b.mu.Lock()
		defer b.mu.Unlock()
		want := map[string]bool{}
		for _, env := range b.deployed {
			for c, v := range env {
				want[c+"@"+v] = true
			}
		}
		if extra := r.URL.Query().Get("include"); extra != "" {
			want[extra] = true
		}
		out := []map[string]any{}
		for key := range want {
			if p, ok := b.pacts[key]; ok {
				out = append(out, map[string]any{"key": key, "hash": contentHash(p), "pact": json.RawMessage(p)})
			}
		}
		sort.Slice(out, func(i, j int) bool { return out[i]["key"].(string) < out[j]["key"].(string) })
		json.NewEncoder(w).Encode(out)
	})
	mux.HandleFunc("POST /verification-results", func(w http.ResponseWriter, r *http.Request) {
		var res struct {
			Hash, ProviderVersion string
			Success               bool
		}
		json.NewDecoder(r.Body).Decode(&res)
		b.mu.Lock()
		b.verifications[res.Hash+"|"+res.ProviderVersion] = res.Success
		b.mu.Unlock()
		w.WriteHeader(http.StatusCreated)
	})
	mux.HandleFunc("POST /environments/{env}/deployments", func(w http.ResponseWriter, r *http.Request) {
		var d struct{ Pacticipant, Version string }
		json.NewDecoder(r.Body).Decode(&d)
		b.mu.Lock()
		b.deployed[r.PathValue("env")][d.Pacticipant] = d.Version
		b.mu.Unlock()
		w.WriteHeader(http.StatusCreated)
	})
	mux.HandleFunc("GET /can-i-deploy", func(w http.ResponseWriter, r *http.Request) {
		q := r.URL.Query()
		ok, reasons := b.canIDeploy(q.Get("pacticipant"), q.Get("version"), q.Get("to"))
		json.NewEncoder(w).Encode(map[string]any{"deployable": ok, "reasons": reasons})
	})
	return mux
}

// canIDeploy walks the matrix: every pair (this app @ version, the OTHER side as deployed in env)
// must have a SUCCESSFUL verification. Missing verification counts as failure.
func (b *Broker) canIDeploy(app, version, env string) (bool, []string) {
	b.mu.Lock()
	defer b.mu.Unlock()
	type pair struct{ consumerKey, providerVersion string }
	var pairs []pair
	if app == "orders-api" { // deploying the provider: check every consumer currently in env
		for c, v := range b.deployed[env] {
			if _, has := b.pacts[c+"@"+v]; has {
				pairs = append(pairs, pair{c + "@" + v, version})
			}
		}
	} else { // deploying a consumer: check against the provider version currently in env
		pv, ok := b.deployed[env]["orders-api"]
		if !ok {
			return false, []string{"orders-api is not deployed to " + env}
		}
		pairs = append(pairs, pair{app + "@" + version, pv})
	}
	sort.Slice(pairs, func(i, j int) bool { return pairs[i].consumerKey < pairs[j].consumerKey })
	all := true
	var reasons []string
	for _, p := range pairs {
		res, verified := b.verifications[contentHash(b.pacts[p.consumerKey])+"|"+p.providerVersion]
		switch {
		case !verified:
			all = false
			reasons = append(reasons, fmt.Sprintf("%s x orders-api@%s: never verified", p.consumerKey, p.providerVersion))
		case !res:
			all = false
			reasons = append(reasons, fmt.Sprintf("%s x orders-api@%s: verification FAILED", p.consumerKey, p.providerVersion))
		default:
			reasons = append(reasons, fmt.Sprintf("%s x orders-api@%s: ok", p.consumerKey, p.providerVersion))
		}
	}
	return all, reasons
}

// ================================================================ provider ===
// orders-api. The /_pact/provider_states route exists ONLY when testMode is on: a production
// build must never let a caller reset its data.
func NewOrdersAPI(version string, testMode bool) http.Handler {
	var mu sync.Mutex
	orders := map[string]map[string]any{}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /orders/{id}", func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		o, ok := orders[r.PathValue("id")]
		mu.Unlock()
		if !ok {
			http.Error(w, `{"detail":"not found"}`, http.StatusNotFound)
			return
		}
		body := map[string]any{"id": o["id"], "status": o["status"], "currency": "USD"}
		switch version {
		case "1.0.0": // original
			body["total_cents"] = o["cents"]
		case "2.0.0": // rename in ONE step: breaks everyone reading total_cents
			body["total"] = map[string]any{"amount": o["cents"], "currency": "USD"}
		case "2.1.0": // EXPAND: add the new shape, keep the old one
			body["total_cents"] = o["cents"]
			body["total"] = map[string]any{"amount": o["cents"], "currency": "USD"}
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(body)
	})
	if testMode {
		mux.HandleFunc("POST /_pact/provider_states", func(w http.ResponseWriter, r *http.Request) {
			var s struct{ State string }
			json.NewDecoder(r.Body).Decode(&s)
			mu.Lock()
			defer mu.Unlock()
			switch s.State {
			case "order 42 exists":
				orders["42"] = map[string]any{"id": 42, "status": "SHIPPED", "cents": 4598}
			default:
				http.Error(w, "unknown provider state "+s.State, http.StatusBadRequest)
			}
		})
	}
	return mux
}

// ================================================================ verifier ===
// What `pact-provider-verifier` / pact-go's VerifyProvider do in a provider's CI job.
func verify(broker, providerVersion string, include string) map[string][]string {
	api := httptest.NewServer(NewOrdersAPI(providerVersion, true)) // the REAL provider, in test mode
	defer api.Close()

	resp, err := http.Get(broker + "/pacts/provider/orders-api/for-verification?include=" + url.QueryEscape(include))
	if err != nil {
		panic(err)
	}
	var toVerify []struct {
		Key, Hash string
		Pact      Pact
	}
	json.NewDecoder(resp.Body).Decode(&toVerify)
	resp.Body.Close()

	results := map[string][]string{}
	for _, tv := range toVerify {
		var errs []string
		for _, in := range tv.Pact.Interactions {
			for _, st := range in.ProviderStates {
				body, _ := json.Marshal(map[string]string{"state": st.Name})
				r, _ := http.Post(api.URL+"/_pact/provider_states", "application/json", bytes.NewReader(body))
				if r.StatusCode != http.StatusOK {
					errs = append(errs, "provider state setup failed: "+st.Name)
				}
				r.Body.Close()
			}
			req, _ := http.NewRequest(in.Request.Method, api.URL+in.Request.Path, nil)
			r, err := http.DefaultClient.Do(req)
			if err != nil {
				panic(err)
			}
			var actual any
			json.NewDecoder(r.Body).Decode(&actual)
			r.Body.Close()
			if r.StatusCode != in.Response.Status {
				errs = append(errs, fmt.Sprintf("status %d, want %d", r.StatusCode, in.Response.Status))
				continue
			}
			match(in.Response.Body, actual, "$", in.Response.MatchingRules["body"], &errs)
		}
		results[tv.Key] = errs
		post(broker+"/verification-results", map[string]any{
			"hash": tv.Hash, "providerVersion": providerVersion, "success": len(errs) == 0})
	}
	return results
}

// ================================================================== helpers ===
func post(u string, v any) {
	b, _ := json.Marshal(v)
	r, err := http.Post(u, "application/json", bytes.NewReader(b))
	if err != nil {
		panic(err)
	}
	r.Body.Close()
}

func put(u string, body []byte) {
	req, _ := http.NewRequest(http.MethodPut, u, bytes.NewReader(body))
	r, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	r.Body.Close()
}

func canIDeploy(broker, app, version string) bool {
	r, err := http.Get(fmt.Sprintf("%s/can-i-deploy?pacticipant=%s&version=%s&to=production", broker, app, version))
	if err != nil {
		panic(err)
	}
	defer r.Body.Close()
	var out struct {
		Deployable bool
		Reasons    []string
	}
	json.NewDecoder(r.Body).Decode(&out)
	verdict := "NO"
	if out.Deployable {
		verdict = "yes"
	}
	fmt.Printf("   can-i-deploy %s@%s to production? %s\n", app, version, verdict)
	for _, reason := range out.Reasons {
		fmt.Printf("        %s\n", reason)
	}
	return out.Deployable
}

func printVerify(v string, res map[string][]string) {
	keys := make([]string, 0, len(res))
	for k := range res {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		status := "PASS"
		if len(res[k]) > 0 {
			status = "FAIL  " + strings.Join(res[k], "; ")
		}
		fmt.Printf("   verify orders-api@%s against %-18s %s\n", v, k, status)
	}
}

func check(cond bool, msg string) {
	if !cond {
		panic("FAILED: " + msg)
	}
}

func main() {
	brokerSrv := httptest.NewServer(NewBroker())
	defer brokerSrv.Close()
	broker := brokerSrv.URL
	deploy := func(app, v string) {
		post(broker+"/environments/production/deployments", map[string]string{"pacticipant": app, "version": v})
		fmt.Printf("   deployed %s@%s to production\n", app, v)
	}

	fmt.Println("== 1. both consumers publish pacts; orders-api 1.0.0 verifies them; everything ships ==")
	put(broker+"/pacts/provider/orders-api/consumer/checkout-web/version/17", pactJSON("checkout-web", "status", "total_cents"))
	put(broker+"/pacts/provider/orders-api/consumer/mobile-app/version/5.2", pactJSON("mobile-app", "total_cents", "currency"))
	printVerify("1.0.0", verify(broker, "1.0.0", "checkout-web@17"))
	verify(broker, "1.0.0", "mobile-app@5.2")
	check(canIDeploy(broker, "orders-api", "1.0.0"), "first provider deploy has no consumers yet")
	deploy("orders-api", "1.0.0")
	check(canIDeploy(broker, "checkout-web", "17"), "checkout 17 was verified by 1.0.0")
	deploy("checkout-web", "17")
	check(canIDeploy(broker, "mobile-app", "5.2"), "mobile 5.2 was verified by 1.0.0")
	deploy("mobile-app", "5.2")

	fmt.Println("\n== 2. orders-api 2.0.0 renames total_cents -> total{amount,currency} in one step ==")
	res := verify(broker, "2.0.0", "")
	printVerify("2.0.0", res)
	check(len(res["checkout-web@17"]) == 1 && strings.Contains(res["checkout-web@17"][0], "$.total_cents: missing"), "rename caught")
	check(!canIDeploy(broker, "orders-api", "2.0.0"), "a breaking provider must be blocked")

	fmt.Println("\n== 3. EXPAND instead: 2.1.0 adds total and keeps total_cents ==")
	printVerify("2.1.0", verify(broker, "2.1.0", ""))
	check(canIDeploy(broker, "orders-api", "2.1.0"), "expand step is safe")
	deploy("orders-api", "2.1.0")

	fmt.Println("\n== 4. checkout-web 18 starts reading the NEW field `total` ==")
	put(broker+"/pacts/provider/orders-api/consumer/checkout-web/version/18", pactJSON("checkout-web", "status", "total"))
	check(!canIDeploy(broker, "checkout-web", "18"), "unverified pact must be a NO")
	fmt.Println("   (the broker fires a webhook: 'pact changed, run orders-api verification for the prod version')")
	printVerify("2.1.0", verify(broker, "2.1.0", "checkout-web@18"))
	check(canIDeploy(broker, "checkout-web", "18"), "verified against the 2.1.0 in prod")
	deploy("checkout-web", "18")

	fmt.Println("\n== 5. identical pact content under a new version reuses the old verification ==")
	put(broker+"/pacts/provider/orders-api/consumer/checkout-web/version/18.0.1", pactJSON("checkout-web", "status", "total"))
	check(canIDeploy(broker, "checkout-web", "18.0.1"), "same content hash, same result")

	fmt.Println("\n== 6. CONTRACT: may 3.0.0 finally drop total_cents? Only when no deployed consumer reads it ==")
	res = verify(broker, "2.0.0", "") // 2.0.0 has exactly the post-contract shape
	printVerify("2.0.0", res)
	check(!canIDeploy(broker, "orders-api", "2.0.0"), "mobile-app 5.2 in prod still reads total_cents")
	fmt.Println("   => the blocker is now named: mobile-app must ship a version that reads `total` first.")

	// production must not expose the provider-state backdoor
	prod := httptest.NewServer(NewOrdersAPI("2.1.0", false))
	defer prod.Close()
	r, _ := http.Post(prod.URL+"/_pact/provider_states", "application/json", strings.NewReader(`{"state":"order 42 exists"}`))
	fmt.Printf("\nPOST /_pact/provider_states on a production build -> %d\n", r.StatusCode)
	check(r.StatusCode == http.StatusNotFound || r.StatusCode == http.StatusMethodNotAllowed, "no backdoor in prod")
	fmt.Println("OK")
}
