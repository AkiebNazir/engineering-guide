/*
LAB 02 (advanced) - From metrics to pages: histogram percentiles, SLOs, multi-window burn-rate alerts
=====================================================================================================
Telemetry is only useful if it wakes the right person at the right time. This lab turns raw
request metrics into the alerting scheme from the Google SRE Workbook, from scratch, on a
simulated 30-day stream of per-minute request counts. Standard library only.

	requests --> counters (total, errors) + latency histogram --> SLI --> error budget --> burn rate --> page / ticket

You will learn

  - why you alert on PERCENTILES from HISTOGRAMS, not on averages: one slow dependency moves p99
    by seconds and the mean by a few milliseconds; and a percentile from buckets is an
    ESTIMATE (linear interpolation inside a bucket, like Prometheus histogram_quantile)

  - that percentiles cannot be averaged across instances, but bucket counts can be SUMMED and the
    percentile computed afterwards

  - SLI / SLO / error budget: 99.9% of requests succeed over 30 days -> 0.1% may fail ->
    about 43 minutes of full outage, or a much longer partial one

  - BURN RATE = observed error ratio / allowed error ratio. Burn rate 1 spends the budget in
    exactly 30 days; 14.4 spends 2% of it in one hour

  - MULTI-WINDOW, MULTI-BURN-RATE alerts: page when BOTH the 1 h and 5 min windows burn > 14.4x
    (fast, and it resets quickly after recovery); open a TICKET when the 6 h and 30 min windows
    burn > 6x (a slow leak that nobody needs to be woken for, but that empties the budget in days);
    and why a naive "error rate > 0.1% for 5 minutes" rule pages on a 2-minute blip and then keeps
    paging for days during a leak (pager fatigue: people learn to ignore it)

Run it   go run ./Observability/labs/golang/02_slo_histograms_and_burn_rate_alerts
*/
package main

import (
	"fmt"
	"math"
	"math/rand"
	"sort"
)

func must(cond bool, msg string) {
	if !cond {
		panic("FAILED: " + msg)
	}
}

// ================================================================== histogram ===
type Histogram struct {
	Bounds []float64 // upper bounds (le), seconds; an implicit +Inf bucket follows
	Counts []uint64  // per bucket (NOT cumulative here; Prometheus exposes cumulative)
	Sum    float64
	Total  uint64
}

func NewHistogram(bounds ...float64) *Histogram {
	return &Histogram{Bounds: bounds, Counts: make([]uint64, len(bounds)+1)}
}

func (h *Histogram) Observe(v float64) {
	i := sort.SearchFloat64s(h.Bounds, v) // first bound >= v
	h.Counts[i]++
	h.Sum += v
	h.Total++
}

// Merge sums bucket counts: the ONLY correct way to combine latency across instances.
func (h *Histogram) Merge(o *Histogram) {
	for i := range h.Counts {
		h.Counts[i] += o.Counts[i]
	}
	h.Sum += o.Sum
	h.Total += o.Total
}

// Quantile interpolates linearly inside the bucket that holds rank q*Total.
func (h *Histogram) Quantile(q float64) float64 {
	rank := q * float64(h.Total)
	var seen float64
	for i, c := range h.Counts {
		if seen+float64(c) >= rank && c > 0 {
			lower := 0.0
			if i > 0 {
				lower = h.Bounds[i-1]
			}
			if i == len(h.Bounds) {
				return h.Bounds[len(h.Bounds)-1] // +Inf bucket: the best we can say is "above the top bound"
			}
			return lower + (h.Bounds[i]-lower)*(rank-seen)/float64(c)
		}
		seen += float64(c)
	}
	return math.NaN()
}

func exactQuantile(xs []float64, q float64) float64 {
	s := append([]float64(nil), xs...)
	sort.Float64s(s)
	return s[int(math.Ceil(q*float64(len(s))))-1]
}

// ==================================================================== SLO math ===
const (
	slo          = 0.999
	budget       = 1 - slo // allowed error ratio
	minutesIn30d = 30 * 24 * 60
)

type minute struct{ total, errors float64 }

// burnRate over the last `window` minutes ending at index end (inclusive).
func burnRate(series []minute, end, window int) float64 {
	var t, e float64
	for i := max(0, end-window+1); i <= end; i++ {
		t += series[i].total
		e += series[i].errors
	}
	if t == 0 {
		return 0
	}
	return (e / t) / budget
}

type alert struct {
	name                  string
	longWin, shortWin     int
	threshold             float64
	firstFired, lastFired int
	firedMinutes          int
}

func (a *alert) eval(series []minute, i int) {
	if burnRate(series, i, a.longWin) > a.threshold && burnRate(series, i, a.shortWin) > a.threshold {
		if a.firstFired < 0 {
			a.firstFired = i
		}
		a.lastFired = i
		a.firedMinutes++
	}
}

func main() {
	rng := rand.New(rand.NewSource(7))

	fmt.Println("== 1. mean vs p99: 2% of calls hit a slow dependency ==")
	h := NewHistogram(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5)
	var raw []float64
	for i := 0; i < 50_000; i++ {
		v := 0.02 + rng.ExpFloat64()*0.01
		if rng.Float64() < 0.02 {
			v = 1.5 + rng.Float64()
		}
		raw = append(raw, v)
		h.Observe(v)
	}
	mean := h.Sum / float64(h.Total)
	fmt.Printf("   mean %.3fs   p50 est %.3fs (exact %.3fs)   p99 est %.3fs (exact %.3fs)\n",
		mean, h.Quantile(0.5), exactQuantile(raw, 0.5), h.Quantile(0.99), exactQuantile(raw, 0.99))
	must(mean < 0.1 && h.Quantile(0.99) > 1, "the mean hides the tail")
	must(math.Abs(h.Quantile(0.99)-exactQuantile(raw, 0.99)) < 1.0, "estimate within its bucket (1 s - 2.5 s)")
	fmt.Println("   the p99 estimate is only as precise as the bucket it falls in: choose bounds near your SLO")

	fmt.Println("\n== 2. combining instances: average the p99s, or merge the buckets? ==")
	fast, slow := NewHistogram(h.Bounds...), NewHistogram(h.Bounds...)
	var all []float64
	for i := 0; i < 9000; i++ {
		v := 0.01 + rng.Float64()*0.03
		fast.Observe(v)
		all = append(all, v)
	}
	for i := 0; i < 1000; i++ {
		v := 0.3 + rng.Float64()*0.6
		slow.Observe(v)
		all = append(all, v)
	}
	avgOfP99 := (fast.Quantile(0.99) + slow.Quantile(0.99)) / 2
	merged := NewHistogram(h.Bounds...)
	merged.Merge(fast)
	merged.Merge(slow)
	fmt.Printf("   average of per-instance p99: %.3fs   merged-bucket p99: %.3fs   exact: %.3fs\n",
		avgOfP99, merged.Quantile(0.99), exactQuantile(all, 0.99))
	must(math.Abs(merged.Quantile(0.99)-exactQuantile(all, 0.99)) < math.Abs(avgOfP99-exactQuantile(all, 0.99)), "merge wins")
	fmt.Println("   PromQL: histogram_quantile(0.99, sum by (le) (rate(http_server_request_duration_seconds_bucket[5m])))")

	fmt.Println("\n== 3. the error budget ==")
	fmt.Printf("   SLO %.1f%% over 30 days -> budget %.2f%% of requests = %.1f minutes of total outage\n",
		slo*100, budget*100, budget*minutesIn30d)
	for _, br := range []float64{1, 2, 6, 14.4, 36} {
		fmt.Printf("   burn rate %5.1f -> budget gone in %6.1f hours;  1 hour spends %4.1f%% of it\n",
			br, 30*24/br, 100*br/(30*24))
	}

	fmt.Println("\n== 4. 30 days of traffic with three incidents ==")
	series := make([]minute, minutesIn30d)
	for i := range series {
		total := 1000 + 400*math.Sin(float64(i)/1440*2*math.Pi) // daily cycle
		errRatio := 0.0002                                      // healthy: 0.02%
		switch {
		case i >= 3*1440 && i < 3*1440+2: // day 3: a 2-minute blip at 1% errors (noise)
			errRatio = 0.01
		case i >= 10*1440 && i < 10*1440+45: // day 10: 45-minute outage, 20% errors
			errRatio = 0.20
		case i >= 20*1440 && i < 24*1440: // days 20-24: a slow leak, 0.8% errors (burn 8x)
			errRatio = 0.008
		}
		series[i] = minute{total, total * errRatio}
	}
	naive := &alert{name: "naive: error rate > 0.1% for 5 min", longWin: 5, shortWin: 5, threshold: 1, firstFired: -1}
	page := &alert{name: "PAGE: 1h & 5m burn > 14.4", longWin: 60, shortWin: 5, threshold: 14.4, firstFired: -1}
	ticket := &alert{name: "TICKET: 6h & 30m burn > 6", longWin: 360, shortWin: 30, threshold: 6, firstFired: -1}
	alerts := []*alert{naive, page, ticket}
	for i := range series {
		for _, a := range alerts {
			a.eval(series, i)
		}
	}
	var spent float64
	for _, m := range series {
		spent += m.errors
	}
	var total float64
	for _, m := range series {
		total += m.total
	}
	fmt.Printf("   budget spent over the month: %.0f%% (the slow leak alone spent more than the outage)\n", 100*(spent/total)/budget)
	day := func(i int) string { return fmt.Sprintf("day %2d %02d:%02d", i/1440, (i%1440)/60, i%60) }
	firedIn := func(a *alert, from, to int) bool {
		for i := from; i < to; i++ {
			if burnRate(series, i, a.longWin) > a.threshold && burnRate(series, i, a.shortWin) > a.threshold {
				return true
			}
		}
		return false
	}
	for _, a := range alerts {
		fmt.Printf("   %-36s first %s, fired %4d minutes; blip:%-5v outage:%-5v leak:%v\n", a.name, day(a.firstFired),
			a.firedMinutes, firedIn(a, 3*1440, 3*1440+10), firedIn(a, 10*1440, 10*1440+60), firedIn(a, 20*1440, 24*1440))
	}
	must(firedIn(naive, 3*1440, 3*1440+10), "naive rule pages on a 2-minute blip")
	must(!firedIn(page, 3*1440, 3*1440+10) && !firedIn(ticket, 3*1440, 3*1440+10), "burn-rate rules ignore the blip")
	must(firedIn(page, 10*1440, 10*1440+60), "outage pages")
	must(!firedIn(page, 20*1440, 24*1440) && firedIn(ticket, 20*1440, 24*1440), "leak -> ticket, not a page")

	// how fast does the page fire, and how fast does it clear after recovery?
	var detect, clear int
	for i := 10 * 1440; ; i++ {
		if burnRate(series, i, 60) > 14.4 && burnRate(series, i, 5) > 14.4 {
			detect = i - 10*1440
			break
		}
	}
	for i := 10*1440 + 45; ; i++ {
		if !(burnRate(series, i, 60) > 14.4 && burnRate(series, i, 5) > 14.4) {
			clear = i - (10*1440 + 45)
			break
		}
	}
	fmt.Printf("   outage: page after %d min; clears %d min after recovery (the 5-min window drops first)\n", detect, clear)
	must(detect <= 5 && clear <= 5, "fast detect, fast reset")

	fmt.Println("\nOK")
}
