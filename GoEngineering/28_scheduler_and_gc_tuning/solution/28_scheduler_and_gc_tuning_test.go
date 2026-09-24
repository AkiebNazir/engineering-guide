package rtune

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"runtime/debug"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

// These tests mutate process-wide runtime settings, so none of them call
// t.Parallel().

const kb = 1 << 10
const mb = 1 << 20

// ----------------------------------------------------------------------------
// GOGC and GOMEMLIMIT
// ----------------------------------------------------------------------------

func TestLowerGOGCRunsMoreCycles(t *testing.T) {
	// ~128 MB allocated in total, ~4 MB live at any moment.
	work := func() { Churn(2000, 64*kb, 64) }

	low := MeasureGC(25, 0, work)
	def := MeasureGC(100, 0, work)
	high := MeasureGC(400, 0, work)

	t.Logf("GOGC=25  cycles=%3d pause=%-10v alloc=%dMB", low.Cycles, low.PauseTotal, low.Allocated/mb)
	t.Logf("GOGC=100 cycles=%3d pause=%-10v alloc=%dMB", def.Cycles, def.PauseTotal, def.Allocated/mb)
	t.Logf("GOGC=400 cycles=%3d pause=%-10v alloc=%dMB", high.Cycles, high.PauseTotal, high.Allocated/mb)

	if !(low.Cycles > def.Cycles && def.Cycles > high.Cycles) {
		t.Fatalf("expected cycles(25) > cycles(100) > cycles(400), got %d, %d, %d",
			low.Cycles, def.Cycles, high.Cycles)
	}
}

func TestMemoryLimitRescuesGOGCOff(t *testing.T) {
	// ~64 MB allocated, ~1 MB live.
	work := func() { Churn(2000, 32*kb, 32) }

	off := MeasureGC(-1, 0, work)
	offWithLimit := MeasureGC(-1, 24*mb, work)

	t.Logf("GOGC=off                  cycles=%d", off.Cycles)
	t.Logf("GOGC=off GOMEMLIMIT=24MiB cycles=%d", offWithLimit.Cycles)

	if off.Cycles != 0 {
		t.Fatalf("GOGC=off without a limit ran %d cycles, want 0", off.Cycles)
	}
	if offWithLimit.Cycles == 0 {
		t.Fatal("GOGC=off with a 24MiB limit and 64MB of allocation should have collected")
	}
}

func TestMeasureGCRestoresSettings(t *testing.T) {
	before := ReadSnapshot()
	MeasureGC(10, 50*mb, func() {})
	after := ReadSnapshot()
	if before.GCPercent != after.GCPercent || before.MemoryLimit != after.MemoryLimit {
		t.Fatalf("settings leaked: before GOGC=%d limit=%d, after GOGC=%d limit=%d",
			before.GCPercent, before.MemoryLimit, after.GCPercent, after.MemoryLimit)
	}
}

// ----------------------------------------------------------------------------
// GOMAXPROCS
// ----------------------------------------------------------------------------

func TestGOMAXPROCSParallelism(t *testing.T) {
	const limit = 3_000_000
	workers := runtime.NumCPU()

	var one, all int
	var tOne, tAll time.Duration
	WithGOMAXPROCS(1, func() {
		start := time.Now()
		one = CountPrimes(limit, workers)
		tOne = time.Since(start)
	})
	WithGOMAXPROCS(workers, func() {
		start := time.Now()
		all = CountPrimes(limit, workers)
		tAll = time.Since(start)
	})

	if one != all || one != 216816 {
		t.Fatalf("prime counts differ or wrong: %d vs %d (want 216816)", one, all)
	}
	t.Logf("%d workers: GOMAXPROCS=1 %v, GOMAXPROCS=%d %v → %.1fx speedup",
		workers, tOne.Round(time.Millisecond), workers, tAll.Round(time.Millisecond),
		float64(tOne)/float64(tAll))

	if got := runtime.GOMAXPROCS(0); got != ReadSnapshot().GOMAXPROCS {
		t.Fatalf("GOMAXPROCS not restored consistently: %d", got)
	}
}

// ----------------------------------------------------------------------------
// Preemption and stacks — with child processes for the fatal cases
// ----------------------------------------------------------------------------

const helperEnv = "RTUNE_HELPER"

// TestMain lets the test binary double as a helper process: when helperEnv is
// set it runs one scenario and exits instead of running tests.
func TestMain(m *testing.M) {
	switch os.Getenv(helperEnv) {
	case "spin":
		runtime.GOMAXPROCS(1)
		var stop atomic.Bool
		done := make(chan uint64)
		go func() { done <- SpinUntil(&stop) }()
		time.Sleep(30 * time.Millisecond) // needs the P back to wake up
		stop.Store(true)
		fmt.Println("spinner iterations:", <-done)
		os.Exit(0)
	case "overflow":
		debug.SetMaxStack(256 * kb)
		fmt.Println(Recurse(1_000_000))
		os.Exit(0)
	}
	os.Exit(m.Run())
}

func runHelper(t *testing.T, scenario, godebug string, timeout time.Duration) (out string, elapsed time.Duration, timedOut bool, err error) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	cmd := exec.CommandContext(ctx, os.Args[0], "-test.run=^$")
	cmd.Env = append(os.Environ(), helperEnv+"="+scenario, "GODEBUG="+godebug)
	start := time.Now()
	b, err := cmd.CombinedOutput()
	return string(b), time.Since(start), ctx.Err() != nil, err
}

func TestLesson_AsyncPreemption(t *testing.T) {
	if testing.Short() {
		t.Skip("spawns child processes")
	}
	out, took, timedOut, err := runHelper(t, "spin", "", 5*time.Second)
	if err != nil || timedOut {
		t.Fatalf("default runtime: spinner starved main (timedOut=%v err=%v)\n%s", timedOut, err, out)
	}
	t.Logf("default (async preemption on): finished in %v — %s", took.Round(time.Millisecond), strings.TrimSpace(out))

	_, took, timedOut, _ = runHelper(t, "spin", "asyncpreemptoff=1", 2*time.Second)
	if !timedOut {
		t.Fatalf("with asyncpreemptoff=1 the tight loop should starve main forever, but it finished in %v", took)
	}
	t.Logf("GODEBUG=asyncpreemptoff=1: still hung after %v, killed", took.Round(time.Millisecond))
}

func TestStackGrowsOnDemand(t *testing.T) {
	snap := ReadSnapshot()
	done := make(chan int)
	go func() { done <- Recurse(100_000) }() // ~100k × ~150B ≈ 15MB of stack
	if got := <-done; got != 100_000 {
		t.Fatalf("Recurse = %d", got)
	}
	t.Logf("goroutine starting stack %d bytes grew to hold 100,000 frames", snap.StartingStackSize)
}

func TestLesson_StackOverflowIsFatal(t *testing.T) {
	if testing.Short() {
		t.Skip("spawns child processes")
	}
	out, _, timedOut, err := runHelper(t, "overflow", "", 20*time.Second)
	if timedOut || err == nil {
		t.Fatalf("expected the child to crash (timedOut=%v err=%v)", timedOut, err)
	}
	if !strings.Contains(out, "stack overflow") {
		t.Fatalf("expected 'stack overflow' in child output, got:\n%.500s", out)
	}
	first := strings.SplitN(out, "\n", 3)
	t.Logf("child died, not panicked: %q / %q", first[0], first[1])
}

// ----------------------------------------------------------------------------
// Container budgets and snapshot
// ----------------------------------------------------------------------------

func TestCgroupAndLimits(t *testing.T) {
	cases := []struct {
		in string
		n  int64
		ok bool
	}{
		{"max\n", 0, false},
		{"536870912\n", 536870912, true},
		{"", 0, false},
		{"garbage", 0, false},
	}
	for _, c := range cases {
		n, ok := ParseCgroupMemoryMax(c.in)
		if n != c.n || ok != c.ok {
			t.Errorf("ParseCgroupMemoryMax(%q) = %d,%v want %d,%v", c.in, n, ok, c.n, c.ok)
		}
	}
	if got := MemoryLimitFor(1000, 10); got != 900 {
		t.Fatalf("MemoryLimitFor(1000,10) = %d", got)
	}
	if got := MemoryLimitFor(1000, 150); got != 0 {
		t.Fatalf("headroom clamps to 100%%: got %d", got)
	}
}

func TestSnapshot(t *testing.T) {
	s := ReadSnapshot()
	if s.GOMAXPROCS < 1 || s.NumCPU < 1 || s.HeapGoal == 0 || s.StartingStackSize == 0 {
		t.Fatalf("implausible snapshot: %+v", s)
	}
	t.Logf("%+v", s)
}

// ----------------------------------------------------------------------------
// Runnable examples
// ----------------------------------------------------------------------------

func ExampleMemoryLimitFor() {
	container, ok := ParseCgroupMemoryMax("536870912\n") // a 512 MiB pod
	if !ok {
		return
	}
	limit := MemoryLimitFor(container, 10)
	fmt.Printf("GOMEMLIMIT=%dMiB\n", limit>>20)
	// Output: GOMEMLIMIT=460MiB
}

func ExampleMeasureGC() {
	work := func() { Churn(1000, 64*kb, 32) }
	frugal := MeasureGC(50, 0, work)
	greedy := MeasureGC(800, 0, work)
	fmt.Println("GOGC=50 collected more often than GOGC=800:", frugal.Cycles > greedy.Cycles)
	// Output: GOGC=50 collected more often than GOGC=800: true
}

func ExampleCountPrimes() {
	fmt.Println(CountPrimes(100, 4), CountPrimes(1_000_000, 8))
	// Output: 25 78498
}
