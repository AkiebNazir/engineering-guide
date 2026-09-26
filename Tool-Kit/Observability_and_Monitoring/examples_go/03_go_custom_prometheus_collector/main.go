package main

import (
	"math/rand"
	"net/http"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

type ExternalSystemCollector struct {
	queueLengthDesc *prometheus.Desc
}

func NewExternalSystemCollector() *ExternalSystemCollector {
	return &ExternalSystemCollector{
		queueLengthDesc: prometheus.NewDesc("external_queue_length", "Length of external queue", nil, nil),
	}
}

func (c *ExternalSystemCollector) Describe(ch chan<- *prometheus.Desc) {
	ch <- c.queueLengthDesc
}

func (c *ExternalSystemCollector) Collect(ch chan<- prometheus.Metric) {
	val := rand.Float64() * 100
	ch <- prometheus.MustNewConstMetric(c.queueLengthDesc, prometheus.GaugeValue, val)
}

func main() {
	registry := prometheus.NewRegistry()
	registry.MustRegister(NewExternalSystemCollector())

	http.Handle("/metrics", promhttp.HandlerFor(registry, promhttp.HandlerOpts{}))
	http.ListenAndServe(":8080", nil)
}
