package main

import (
	"fmt"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// 1. Define Metrics
var (
	httpRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests processed, labeled by status code.",
		},
		[]string{"status_code"},
	)
	activeConnections = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "active_connections",
			Help: "Number of active connections right now.",
		},
	)
)

func init() {
	// 2. Register metrics with the global registry
	prometheus.MustRegister(httpRequestsTotal)
	prometheus.MustRegister(activeConnections)
}

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		activeConnections.Inc()
		defer activeConnections.Dec()

		time.Sleep(100 * time.Millisecond) // Simulate work

		httpRequestsTotal.WithLabelValues("200").Inc()
		fmt.Fprintf(w, "Hello, Observability!")
	})

	// 3. Expose the /metrics endpoint for Prometheus to scrape
	http.Handle("/metrics", promhttp.Handler())

	fmt.Println("Server listening on :8080. Check out http://localhost:8080/metrics")
	http.ListenAndServe(":8080", nil)
}
