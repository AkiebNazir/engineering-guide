package tracing

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"testing"
	"time"
)

func sampleOrders(n int) []Order {
	orders := make([]Order, n)
	for i := range orders {
		orders[i] = Order{ID: i + 1, Items: 1 + i%5}
	}
	return orders
}

// ----------------------------------------------------------------------------
// Execution trace
// ----------------------------------------------------------------------------

func TestTraceToCapturesPipeline(t *testing.T) {
	var buf bytes.Buffer
	var results []Result
	err := TraceTo(&buf, func() {
		results = ProcessOrders(context.Background(), sampleOrders(40), 4)
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 40 || results[0].ID != 1 || results[39].ID != 40 {
		t.Fatalf("results out of order or missing: %d", len(results))
	}
	if !bytes.HasPrefix(buf.Bytes(), []byte("go 1.")) {
		t.Fatalf("not an execution trace; header %q", buf.Bytes()[:min(16, buf.Len())])
	}
	for _, want := range []string{"processOrder", "validate", "price", "persist"} {
		if !bytes.Contains(buf.Bytes(), []byte(want)) {
			t.Errorf("trace does not mention %q", want)
		}
	}
	t.Logf("trace: %d KB, header %q — open with: go tool trace trace.out",
		buf.Len()>>10, strings.TrimRight(string(buf.Bytes()[:14]), "\x00"))

	// Only one trace at a time.
	nested := TraceTo(io.Discard, func() {})
	if err := TraceTo(io.Discard, func() {
		nested = TraceTo(io.Discard, func() {})
	}); err != nil {
		t.Fatal(err)
	}
	if nested == nil {
		t.Fatal("a second concurrent trace.Start should fail")
	}
}

func TestProcessOrdersResultsIndependentOfTracing(t *testing.T) {
	a := ProcessOrders(context.Background(), sampleOrders(10), 3)
	var b []Result
	_ = TraceTo(io.Discard, func() { b = ProcessOrders(context.Background(), sampleOrders(10), 1) })
	for i := range a {
		if a[i] != b[i] {
			t.Fatalf("result %d differs: %+v vs %+v", i, a[i], b[i])
		}
	}
}

// ----------------------------------------------------------------------------
// CPU profile → go tool pprof
// ----------------------------------------------------------------------------

func TestLesson_CPUProfileFindsHotFunction(t *testing.T) {
	if testing.Short() {
		t.Skip("runs go tool pprof")
	}
	gobin, err := exec.LookPath("go")
	if err != nil {
		t.Skip("go not on PATH")
	}
	path := filepath.Join(t.TempDir(), "cpu.pprof")
	f, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	// Heavier orders than sampleOrders so pricing (~1M iterations each) is
	// comparable to the 1ms persist sleep; with tiny orders the profile is
	// almost entirely idle runtime frames and priceOrder may get no samples.
	heavy := make([]Order, 16)
	for i := range heavy {
		heavy[i] = Order{ID: i, Items: 50}
	}
	err = ProfileCPU(f, func() {
		deadline := time.Now().Add(400 * time.Millisecond)
		for time.Now().Before(deadline) {
			ProcessOrders(context.Background(), heavy, runtime.NumCPU())
		}
	})
	f.Close()
	if err != nil {
		t.Fatal(err)
	}

	out, err := exec.Command(gobin, "tool", "pprof", "-top", "-nodecount=8", path).CombinedOutput()
	if err != nil {
		t.Fatalf("pprof: %v\n%s", err, out)
	}
	// priceOrder must be the hottest APPLICATION function. The top rows are
	// often runtime frames (pthread_cond_wait, findRunnable): idle threads
	// parking because this pipeline mostly SLEEPS in persist — and that sleep
	// time itself never appears, because CPU profiles only see on-CPU time.
	if !strings.Contains(string(out), "priceOrder") {
		t.Fatalf("expected priceOrder among the top CPU consumers:\n%s", out)
	}
	t.Logf("go tool pprof -top:\n%s", out)
}

// ----------------------------------------------------------------------------
// Mutex / block / goroutine profiles
// ----------------------------------------------------------------------------

func TestContentionProfileAttributesTheLockHolder(t *testing.T) {
	prof, err := ContentionProfile(func() { ContendedWork(8, 300) })
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(prof, "ContendedWork") {
		t.Fatalf("mutex profile does not mention ContendedWork:\n%.1500s", prof)
	}
	if runtime.SetMutexProfileFraction(-1) != 0 {
		t.Fatal("mutex profile fraction not restored")
	}
}

func TestBlockProfileSeesChannelWaits(t *testing.T) {
	prof, err := BlockProfile(func() {
		ch := make(chan int)
		var wg sync.WaitGroup
		wg.Go(func() {
			for range 50 {
				<-ch
			}
		})
		for i := range 50 {
			time.Sleep(100 * time.Microsecond)
			ch <- i
		}
		wg.Wait()
	})
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(prof, "runtime.chanrecv") && !strings.Contains(prof, "runtime.chansend") {
		t.Fatalf("block profile has no channel events:\n%.1500s", prof)
	}
}

func TestLesson_GoroutineProfileCatchesLeak(t *testing.T) {
	// Profile symbols use the IMPORT PATH, whose last element here is
	// "solution" — not the package name "tracing". Match on the function.
	const marker = "LeakyFanOut.func1"
	before, err := GoroutinesMatching(marker)
	if err != nil {
		t.Fatal(err)
	}
	LeakyFanOut(20)
	time.Sleep(20 * time.Millisecond) // let all senders reach their blocking send
	after, _ := GoroutinesMatching(marker)
	leaked := after - before
	if leaked != 19 {
		t.Fatalf("expected 19 leaked goroutines, profile shows %d", leaked)
	}
	t.Logf("LeakyFanOut(20): goroutine profile shows %d goroutines stuck in %s", leaked, marker)

	fixedBefore, _ := GoroutinesMatching("FixedFanOut.func1")
	FixedFanOut(20)
	time.Sleep(20 * time.Millisecond)
	fixedAfter, _ := GoroutinesMatching("FixedFanOut.func1")
	if fixedAfter-fixedBefore != 0 {
		t.Fatalf("FixedFanOut left %d goroutines", fixedAfter-fixedBefore)
	}
}

// ----------------------------------------------------------------------------
// Scheduler latency
// ----------------------------------------------------------------------------

func TestLesson_SchedulerLatencyUnderCPUSaturation(t *testing.T) {
	// 20 goroutines that each want to wake 10 times.
	sleepers := func() {
		var wg sync.WaitGroup
		for range 20 {
			wg.Go(func() {
				for range 10 {
					time.Sleep(100 * time.Microsecond)
				}
			})
		}
		wg.Wait()
	}

	idle := MeasureSchedLatency(sleepers)

	prev := runtime.GOMAXPROCS(1)
	defer runtime.GOMAXPROCS(prev)
	stop := make(chan struct{})
	var hogs sync.WaitGroup
	for range 4 { // CPU hogs competing for the single P
		hogs.Go(func() {
			for {
				select {
				case <-stop:
					return
				default:
					priceOrder(Order{ID: 1, Items: 1})
				}
			}
		})
	}
	loaded := MeasureSchedLatency(sleepers)
	close(stop)
	hogs.Wait()

	t.Logf("idle   (GOMAXPROCS=%d): p50=%-10v p99=%-10v samples=%d", prev, idle.P50, idle.P99, idle.Samples)
	t.Logf("loaded (GOMAXPROCS=1, 4 CPU hogs): p50=%-10v p99=%-10v samples=%d", loaded.P50, loaded.P99, loaded.Samples)
	if idle.Samples == 0 || loaded.Samples == 0 {
		t.Fatal("no scheduler latency samples recorded")
	}
	if loaded.P99 <= idle.P99 {
		t.Fatalf("expected runnable-wait p99 to rise under CPU saturation: idle %v, loaded %v", idle.P99, loaded.P99)
	}
}

// ----------------------------------------------------------------------------
// Flight recorder
// ----------------------------------------------------------------------------

func TestSlowRequestCaptureSnapshotsOnlySlowRequests(t *testing.T) {
	var mu sync.Mutex
	var snapshots [][]byte
	capture, err := NewSlowRequestCapture(50*time.Millisecond, time.Hour, func(b []byte) {
		mu.Lock()
		snapshots = append(snapshots, b)
		mu.Unlock()
	})
	if err != nil {
		t.Fatal(err)
	}
	defer capture.Stop()

	handler := capture.Middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("slow") == "1" {
			ProcessOrders(r.Context(), sampleOrders(8), 2)
			time.Sleep(60 * time.Millisecond)
		}
		_, _ = io.WriteString(w, "ok")
	}))
	srv := httptest.NewServer(handler)
	defer srv.Close()

	get := func(q string) {
		resp, err := http.Get(srv.URL + q)
		if err != nil {
			t.Fatal(err)
		}
		_, _ = io.Copy(io.Discard, resp.Body)
		resp.Body.Close()
	}
	for range 5 {
		get("/")
	}
	mu.Lock()
	fast := len(snapshots)
	mu.Unlock()
	get("/?slow=1")
	get("/?slow=1") // rate-limited by minGap: no second snapshot

	mu.Lock()
	defer mu.Unlock()
	if fast != 0 || len(snapshots) != 1 {
		t.Fatalf("snapshots after fast=%d, after slow=%d; want 0 then 1", fast, len(snapshots))
	}
	if !bytes.HasPrefix(snapshots[0], []byte("go 1.")) || !bytes.Contains(snapshots[0], []byte("processOrder")) {
		t.Fatalf("snapshot is not a trace of the slow request (%d bytes)", len(snapshots[0]))
	}
	t.Logf("slow request → flight recorder snapshot of %d KB containing the processOrder tasks", len(snapshots[0])>>10)
}

// ----------------------------------------------------------------------------
// Benchmark — what does instrumentation cost when tracing is OFF?
// ----------------------------------------------------------------------------

func BenchmarkProcessOrdersTracingOff(b *testing.B) {
	orders := sampleOrders(4)
	for b.Loop() {
		ProcessOrders(context.Background(), orders, 2)
	}
}

func BenchmarkProcessOrdersTracingOn(b *testing.B) {
	orders := sampleOrders(4)
	_ = TraceTo(io.Discard, func() {
		for b.Loop() {
			ProcessOrders(context.Background(), orders, 2)
		}
	})
}

// ----------------------------------------------------------------------------
// Runnable examples
// ----------------------------------------------------------------------------

func ExampleProcessOrders() {
	res := ProcessOrders(context.Background(), []Order{{ID: 7, Items: 1}, {ID: 8, Items: 2}}, 2)
	fmt.Println(len(res), res[0].ID, res[1].ID)
	// Output: 2 7 8
}

func ExampleGoroutinesMatching() {
	n, _ := GoroutinesMatching("ExampleGoroutinesMatching")
	fmt.Println(n >= 1) // the example's own goroutine is on the stack
	// Output: true
}
