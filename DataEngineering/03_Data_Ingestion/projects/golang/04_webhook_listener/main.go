package main

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/google/uuid"
)

type WebhookHandler struct {
	S3Client *s3.Client
	Bucket   string
}

func (h *WebhookHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
		return
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Failed to read body", http.StatusInternalServerError)
		return
	}
	defer r.Body.Close()

	if len(body) == 0 {
		http.Error(w, "Empty payload", http.StatusBadRequest)
		return
	}

	key := fmt.Sprintf("webhooks/%s_%s.json", time.Now().Format("20060102150405"), uuid.New().String())

	_, err = h.S3Client.PutObject(r.Context(), &s3.PutObjectInput{
		Bucket:      aws.String(h.Bucket),
		Key:         aws.String(key),
		Body:        bytes.NewReader(body),
		ContentType: aws.String("application/json"),
	})

	if err != nil {
		log.Printf("Failed to upload to S3: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	log.Printf("Received webhook, saved to s3://%s/%s", h.Bucket, key)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "success"}`))
}

func main() {
	log.Println("Starting Data Engineering Project: 04_webhook_listener (AWS S3 Backend)")

	bucket := os.Getenv("S3_BUCKET")
	if bucket == "" {
		bucket = "my-webhook-payloads"
	}

	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		log.Fatalf("unable to load SDK config, %v", err)
	}

	s3Client := s3.NewFromConfig(cfg)

	handler := &WebhookHandler{
		S3Client: s3Client,
		Bucket:   bucket,
	}

	http.Handle("/webhook", handler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Listening for webhooks on port %s...", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}
