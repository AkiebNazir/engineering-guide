package main

import (
	"net/http"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	httpRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests.",
		},
		[]string{"path"},
	)
)

func helloHandler(w http.ResponseWriter, r *http.Request) {
	httpRequestsTotal.WithLabelValues(r.URL.Path).Inc()
	w.Write([]byte("Hello, Observability!"))
}

func main() {
	http.Handle("/metrics", promhttp.Handler())
	http.HandleFunc("/", helloHandler)
	http.ListenAndServe(":8080", nil)
}
