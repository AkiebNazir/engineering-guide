package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	pb "secure_gateway/pb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// Global gRPC Client
var cacheClient pb.SemanticCacheServiceClient

func initGRPCClient() {
	// Connect to the Python Semantic Cache gRPC service
	conn, err := grpc.NewClient("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Failed to connect to gRPC server: %v", err)
	}
	cacheClient = pb.NewSemanticCacheServiceClient(conn)
	log.Println("Connected to Semantic Cache gRPC Server at :50051")
}

func handleQuery(w http.ResponseWriter, r *http.Request) {
	prompt := r.URL.Query().Get("prompt")
	if prompt == "" {
		http.Error(w, "prompt query parameter is required", http.StatusBadRequest)
		return
	}

	start := time.Now()

	// 1. Check Semantic Cache via gRPC
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	cacheRes, err := cacheClient.CheckCache(ctx, &pb.CacheRequest{Prompt: prompt})
	if err != nil {
		log.Printf("gRPC cache check failed: %v", err)
		// Proceed to live upstream call if cache fails (Resiliency)
	} else if cacheRes.GetHit() {
		log.Printf("CACHE HIT (Score: %.2f) Latency: %v", cacheRes.GetSimilarityScore(), time.Since(start))
		fmt.Fprintf(w, "Cached Response: %s\n", cacheRes.GetCachedResponse())
		return
	}

	log.Printf("CACHE MISS: Routing to upstream LLM. %v", time.Since(start))
	
	// 2. Call Upstream LLM (Simulated for this capstone)
	// In production, this would make an HTTP call to OpenAI/vLLM
	time.Sleep(500 * time.Millisecond) // Simulating LLM latency
	upstreamResponse := fmt.Sprintf("Live generated response for: %s", prompt)

	// 3. Set Cache asynchronously (Fire-and-forget)
	go func(p, r string) {
		bgCtx, bgCancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer bgCancel()
		_, err := cacheClient.SetCache(bgCtx, &pb.SetCacheRequest{Prompt: p, Response: r})
		if err != nil {
			log.Printf("Background cache write failed: %v", err)
		} else {
			log.Printf("Successfully cached new response for: '%s'", p)
		}
	}(prompt, upstreamResponse)

	fmt.Fprintf(w, "Live Response: %s\n", upstreamResponse)
}

func main() {
	// Initialize the gRPC connection
	initGRPCClient()

	// Start the HTTP API Gateway
	http.HandleFunc("/v1/query", handleQuery)
	log.Println("Golang AI Gateway running on :8080...")
	
	server := &http.Server{
		Addr:         ":8080",
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
	}
	log.Fatal(server.ListenAndServe())
}
