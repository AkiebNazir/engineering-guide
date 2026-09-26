package main

import (
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	pipelineDuration = prometheus.NewSummaryVec(
		prometheus.SummaryOpts{
			Name: "pipeline_processing_seconds",
			Help: "Time spent processing pipeline tasks",
		},
		[]string{"task_name"},
	)
	pipelineStatus = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pipeline_task_status_total",
			Help: "Count of pipeline task statuses",
		},
		[]string{"task_name", "status"},
	)
)

func init() {
	// Register metrics with Prometheus's default registry.
	prometheus.MustRegister(pipelineDuration)
	prometheus.MustRegister(pipelineStatus)
}

func executeTask(taskName string) error {
	log.Printf("Executing task: %s\n", taskName)

	start := time.Now()
	defer func() {
		pipelineDuration.WithLabelValues(taskName).Observe(time.Since(start).Seconds())
	}()

	// Simulate processing time
	time.Sleep(time.Duration(500+rand.Intn(1500)) * time.Millisecond)

	// Simulate occasional failures
	if rand.Float32() < 0.2 {
		pipelineStatus.WithLabelValues(taskName, "failed").Inc()
		log.Printf("Task failed: %s\n", taskName)
		return fmt.Errorf("task %s encountered an error", taskName)
	}

	pipelineStatus.WithLabelValues(taskName, "success").Inc()
	log.Printf("Task completed: %s\n", taskName)
	return nil
}

func runPipeline() {
	tasks := []string{"Extract", "Transform", "Load"}
	for _, task := range tasks {
		err := executeTask(task)
		if err != nil {
			log.Printf("Pipeline halted due to error: %v\n", err)
			break
		}
	}
	log.Println("Pipeline run finished.")
}

func main() {
	rand.Seed(time.Now().UnixNano())

	// Expose the registered metrics via HTTP.
	// Data Engineers use Prometheus + Grafana to scrape these metrics
	http.Handle("/metrics", promhttp.Handler())
	
	// Start metrics server in a goroutine
	go func() {
		log.Println("Starting Prometheus metrics server on :8000")
		if err := http.ListenAndServe(":8000", nil); err != nil {
			log.Fatalf("Error starting HTTP server: %v", err)
		}
	}()

	// Continuously run pipeline to generate metrics
	for {
		runPipeline()
		log.Println("Sleeping before next pipeline run...")
		time.Sleep(5 * time.Second)
	}
}
