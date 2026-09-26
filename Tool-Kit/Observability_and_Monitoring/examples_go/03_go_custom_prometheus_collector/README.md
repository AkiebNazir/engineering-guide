# Go Custom Prometheus Collector
When scraping metrics from a 3rd party system, you should implement the `prometheus.Collector` interface rather than directly setting gauge values.
