/*
LAB 01 (basic) - OpenTelemetry in Go: tracing + metrics middleware, and the context.Context rule
================================================================================================
Python lab 01 instrumented three services by hand. This lab builds the two pieces Go services
actually use - a SERVER middleware and a CLIENT http.RoundTripper, i.e. what otelhttp does - with
the real OpenTelemetry Go SDK, exporting to IN-MEMORY exporters so it runs with nothing installed.

	client -> [ mw ] frontend --RoundTripper--> [ mw ] inventory --RoundTripper--> [ mw ] pricing
	           server span        client span       server span       client span     server span
	           + metrics          + inject header   + metrics         + inject        + metrics

You will learn

  - the Go rule that decides whether your traces work: the current span lives in
    context.Context. A downstream call made with r.Context() joins the trace; the SAME call made
    with context.Background() silently starts a NEW trace (the lab shows both)

  - propagation.TraceContext{} + propagation.Baggage{}: Inject into outgoing headers in the
    RoundTripper, Extract from incoming headers in the middleware

  - span kinds, attributes (semantic-convention keys), RecordError + SetStatus(codes.Error)

  - metrics with the SDK: a Float64Histogram `http.server.request.duration` (seconds, explicit
    buckets) and an Int64UpDownCounter `http.server.active_requests`, read with a ManualReader
    (the pull model a Prometheus exporter uses)

  - that instrumentation is cheap when it is off: with a NeverSample sampler, spans are still
    created for propagation but nothing is recorded or exported

Run it   go run ./Observability/labs/golang/01_otel_middleware_and_context_propagation
*/
package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"sort"
	"strings"
	"time"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/baggage"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/metric"
	"go.opentelemetry.io/otel/propagation"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/metric/metricdata"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
	"go.opentelemetry.io/otel/trace"
)

var (
	spans      = tracetest.NewInMemoryExporter() // shared "collector"
	propagator = propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{})
)

// Service bundles what each process would own: providers with its service.name resource.
type Service struct {
	Name     string
	tracer   trace.Tracer
	tp       *sdktrace.TracerProvider
	reader   *sdkmetric.ManualReader
	duration metric.Float64Histogram
	active   metric.Int64UpDownCounter
	client   *http.Client
}

func NewService(name string, sampler sdktrace.Sampler) *Service {
	res := resource.NewSchemaless(attribute.String("service.name", name))
	tp := sdktrace.NewTracerProvider(sdktrace.WithResource(res), sdktrace.WithSampler(sampler),
		sdktrace.WithSyncer(spans)) // Syncer = export on End(); production uses WithBatcher(otlpExporter)
	reader := sdkmetric.NewManualReader()
	mp := sdkmetric.NewMeterProvider(sdkmetric.WithResource(res), sdkmetric.WithReader(reader))
	meter := mp.Meter("lab")
	dur, _ := meter.Float64Histogram("http.server.request.duration", metric.WithUnit("s"),
		metric.WithExplicitBucketBoundaries(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1))
	act, _ := meter.Int64UpDownCounter("http.server.active_requests", metric.WithUnit("{request}"))
	s := &Service{Name: name, tracer: tp.Tracer("lab"), tp: tp, reader: reader, duration: dur, active: act}
	s.client = &http.Client{Transport: &tracingTransport{s: s, base: http.DefaultTransport}, Timeout: 3 * time.Second}
	return s
}

// ================================================================== server middleware ===
type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (r *statusRecorder) WriteHeader(code int) { r.status = code; r.ResponseWriter.WriteHeader(code) }

// Middleware: extract the caller's context, start a SERVER span, record RED metrics.
func (s *Service) Middleware(route string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ctx := propagator.Extract(r.Context(), propagation.HeaderCarrier(r.Header))
		ctx, span := s.tracer.Start(ctx, r.Method+" "+route, trace.WithSpanKind(trace.SpanKindServer),
			trace.WithAttributes(attribute.String("http.request.method", r.Method),
				attribute.String("http.route", route), attribute.String("url.path", r.URL.Path)))
		defer span.End()

		common := metric.WithAttributes(attribute.String("http.request.method", r.Method), attribute.String("http.route", route))
		s.active.Add(ctx, 1, common)
		defer s.active.Add(ctx, -1, common)

		rec := &statusRecorder{ResponseWriter: w, status: 200}
		start := time.Now()
		next.ServeHTTP(rec, r.WithContext(ctx)) // the span now travels in r.Context()
		span.SetAttributes(attribute.Int("http.response.status_code", rec.status))
		if rec.status >= 500 {
			span.SetStatus(codes.Error, http.StatusText(rec.status))
		}
		s.duration.Record(ctx, time.Since(start).Seconds(), metric.WithAttributes(
			attribute.String("http.request.method", r.Method), attribute.String("http.route", route),
			attribute.Int("http.response.status_code", rec.status)))
	})
}

// ================================================================== client transport ===
type tracingTransport struct {
	s    *Service
	base http.RoundTripper
}

func (t *tracingTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	ctx, span := t.s.tracer.Start(req.Context(), req.Method, trace.WithSpanKind(trace.SpanKindClient),
		trace.WithAttributes(attribute.String("url.full", req.URL.String())))
	defer span.End()
	req = req.Clone(ctx)
	propagator.Inject(ctx, propagation.HeaderCarrier(req.Header)) // traceparent + baggage
	resp, err := t.base.RoundTrip(req)
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return nil, err
	}
	span.SetAttributes(attribute.Int("http.response.status_code", resp.StatusCode))
	if resp.StatusCode >= 500 {
		span.SetStatus(codes.Error, resp.Status)
	}
	return resp, nil
}

func (s *Service) get(ctx context.Context, url string) (int, string, error) {
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	resp, err := s.client.Do(req)
	if err != nil {
		return 0, "", err
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, string(b), nil
}

// ======================================================================== helpers ===
func must(cond bool, msg string) {
	if !cond {
		panic("FAILED: " + msg)
	}
}

func svcName(s tracetest.SpanStub) string {
	for _, kv := range s.Resource.Attributes() {
		if kv.Key == "service.name" {
			return kv.Value.AsString()
		}
	}
	return "?"
}

func printTree(stubs tracetest.SpanStubs) {
	children := map[trace.SpanID][]tracetest.SpanStub{}
	var roots []tracetest.SpanStub
	known := map[trace.SpanID]bool{}
	for _, s := range stubs {
		known[s.SpanContext.SpanID()] = true
	}
	for _, s := range stubs {
		if s.Parent.IsValid() && known[s.Parent.SpanID()] {
			children[s.Parent.SpanID()] = append(children[s.Parent.SpanID()], s)
		} else {
			roots = append(roots, s)
		}
	}
	var walk func([]tracetest.SpanStub, int)
	walk = func(list []tracetest.SpanStub, depth int) {
		sort.Slice(list, func(i, j int) bool { return list[i].StartTime.Before(list[j].StartTime) })
		for _, s := range list {
			status := ""
			if s.Status.Code == codes.Error {
				status = "  ERROR " + s.Status.Description
			}
			fmt.Printf("   %s%-9s %-7s %-22s trace=%s%s\n", strings.Repeat("  ", depth), svcName(s),
				s.SpanKind, s.Name, s.SpanContext.TraceID().String()[:8], status)
			walk(children[s.SpanContext.SpanID()], depth+1)
		}
	}
	walk(roots, 0)
}

func traceIDs(stubs tracetest.SpanStubs) map[string]bool {
	out := map[string]bool{}
	for _, s := range stubs {
		out[s.SpanContext.TraceID().String()] = true
	}
	return out
}

func histogram(s *Service) []metricdata.HistogramDataPoint[float64] {
	var rm metricdata.ResourceMetrics
	s.reader.Collect(context.Background(), &rm)
	for _, sm := range rm.ScopeMetrics {
		for _, m := range sm.Metrics {
			if h, ok := m.Data.(metricdata.Histogram[float64]); ok && m.Name == "http.server.request.duration" {
				return h.DataPoints
			}
		}
	}
	return nil
}

func main() {
	pricing := NewService("pricing", sdktrace.ParentBased(sdktrace.AlwaysSample()))
	inventory := NewService("inventory", sdktrace.ParentBased(sdktrace.AlwaysSample()))
	frontend := NewService("frontend", sdktrace.ParentBased(sdktrace.AlwaysSample()))

	pricingSrv := httptest.NewServer(pricing.Middleware("/price/{sku}", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		sku := strings.TrimPrefix(r.URL.Path, "/price/")
		// baggage set at the edge arrives here, two hops later
		tier := baggage.FromContext(r.Context()).Member("customer.tier").Value()
		trace.SpanFromContext(r.Context()).SetAttributes(attribute.String("customer.tier", tier))
		if sku == "broken" {
			err := errors.New("price table missing for sku")
			trace.SpanFromContext(r.Context()).RecordError(err)
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		fmt.Fprintf(w, "1999 (tier=%s)", tier)
	})))
	defer pricingSrv.Close()

	inventorySrv := httptest.NewServer(inventory.Middleware("/stock/{sku}", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		sku := strings.TrimPrefix(r.URL.Path, "/stock/")
		ctx := r.Context()
		if r.URL.Query().Get("bug") == "1" {
			ctx = context.Background() // THE BUG: the span in r.Context() is dropped here
		}
		_, dbSpan := inventory.tracer.Start(r.Context(), "SELECT stock", trace.WithAttributes(attribute.String("db.system.name", "postgresql")))
		time.Sleep(2 * time.Millisecond)
		dbSpan.End()
		code, body, err := inventory.get(ctx, pricingSrv.URL+"/price/"+sku)
		if err != nil || code != 200 {
			http.Error(w, "pricing failed", http.StatusBadGateway)
			return
		}
		fmt.Fprintf(w, "in stock, %s", body)
	})))
	defer inventorySrv.Close()

	frontendSrv := httptest.NewServer(frontend.Middleware("/product/{sku}", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		m, _ := baggage.NewMember("customer.tier", "gold")
		bag, _ := baggage.New(m)
		ctx := baggage.ContextWithBaggage(r.Context(), bag)
		code, body, err := frontend.get(ctx, inventorySrv.URL+strings.Replace(r.URL.RequestURI(), "/product/", "/stock/", 1))
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadGateway)
			return
		}
		w.WriteHeader(code)
		io.WriteString(w, body)
	})))
	defer frontendSrv.Close()

	call := func(path string) (int, string) {
		resp, err := http.Get(frontendSrv.URL + path)
		if err != nil {
			panic(err)
		}
		defer resp.Body.Close()
		b, _ := io.ReadAll(resp.Body)
		return resp.StatusCode, strings.TrimSpace(string(b))
	}

	fmt.Println("== 1. one request, context passed correctly ==")
	code, body := call("/product/kettle")
	stubs := spans.GetSpans()
	printTree(stubs)
	fmt.Printf("   response %d %q\n", code, body)
	must(code == 200 && len(stubs) == 6 && len(traceIDs(stubs)) == 1, "6 spans, one trace")
	must(strings.Contains(body, "tier=gold"), "baggage travelled two hops")

	fmt.Println("\n== 2. the same request with context.Background() in inventory ==")
	spans.Reset()
	call("/product/kettle?bug=1")
	stubs = spans.GetSpans()
	printTree(stubs)
	fmt.Printf("   %d spans, %d trace ids: the pricing hop became an orphan trace\n", len(stubs), len(traceIDs(stubs)))
	must(len(traceIDs(stubs)) == 2, "trace split in two")
	fmt.Println("   (and the baggage was lost too: tier is empty. go vet cannot catch this - code review and")
	fmt.Println("    the contextcheck linter can. Rule: every call that does I/O takes the ctx you were given.)")

	fmt.Println("\n== 3. an error two hops down ==")
	spans.Reset()
	code, _ = call("/product/broken")
	stubs = spans.GetSpans()
	printTree(stubs)
	var origin string
	for _, s := range stubs {
		for _, e := range s.Events {
			if e.Name == "exception" {
				origin = svcName(s)
			}
		}
	}
	fmt.Printf("   client got %d; the exception event lives on the %s span\n", code, origin)
	must(code == 502 && origin == "pricing", "error located")

	fmt.Println("\n== 4. metrics: read the histogram like a Prometheus scrape would ==")
	for i := 0; i < 20; i++ {
		call("/product/kettle")
	}
	for _, dp := range histogram(frontend) {
		status, _ := dp.Attributes.Value("http.response.status_code")
		fmt.Printf("   frontend http.server.request.duration{status=%d} count=%d sum=%.3fs buckets=%v\n",
			status.AsInt64(), dp.Count, dp.Sum, dp.BucketCounts)
	}
	var total uint64
	for _, dp := range histogram(frontend) {
		total += dp.Count
	}
	must(total == 23, "3 + 20 requests recorded")

	fmt.Println("\n== 5. sampling off: still propagates, records nothing ==")
	spans.Reset()
	quiet := NewService("quiet", sdktrace.NeverSample())
	ctx, span := quiet.tracer.Start(context.Background(), "root")
	carrier := propagation.MapCarrier{}
	propagator.Inject(ctx, carrier)
	span.End()
	fmt.Printf("   recording=%v, exported spans=%d, outgoing traceparent=%s\n",
		span.IsRecording(), len(spans.GetSpans()), carrier["traceparent"])
	must(!span.IsRecording() && len(spans.GetSpans()) == 0 && strings.HasSuffix(carrier["traceparent"], "-00"), "not sampled")

	for _, s := range []*Service{pricing, inventory, frontend, quiet} {
		s.tp.Shutdown(context.Background())
	}
	fmt.Println("\nOK")
}
