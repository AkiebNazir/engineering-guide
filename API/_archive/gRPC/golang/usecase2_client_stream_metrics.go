package main

import (
	"io"
	"log"
)

// Concept for Client Streaming
type pbStreamMetricsServer interface {
	Recv() (*Metric, error)
	SendAndClose(*Ack) error
}
type Metric struct { ServiceId string; CpuUsage float32; MemUsage float32 }
type Ack struct { Success bool; ProcessedCount int32 }

type server struct{}

func (s *server) StreamMetrics(stream pbStreamMetricsServer) error {
	var totalMetrics int32
	
	for {
		metric, err := stream.Recv()
		if err == io.EOF {
			return stream.SendAndClose(&Ack{Success: true, ProcessedCount: totalMetrics})
		}
		if err != nil {
			return err
		}
		
		log.Printf("Received metric: CPU=%f, Mem=%f from %s", metric.CpuUsage, metric.MemUsage, metric.ServiceId)
		totalMetrics++
	}
}

func main() {
	// Register grpc server and implementation...
}
