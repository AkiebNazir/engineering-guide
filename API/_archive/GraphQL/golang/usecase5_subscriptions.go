package main

import (
	"fmt"
	"time"
)

// In Go, GraphQL subscriptions require complex websocket handling (e.g. using github.com/99designs/gqlgen).
// This is a conceptual implementation of the generator/resolver logic.

func CountSubscriptionResolver(target int) <-chan int {
	ch := make(chan int)
	go func() {
		defer close(ch)
		for i := 1; i <= target; i++ {
			ch <- i
			time.Sleep(1 * time.Second)
		}
	}()
	return ch
}

func main() {
	fmt.Println("Starting GraphQL Subscription stream for 'count'...")
	
	// Simulate the GraphQL execution engine consuming the subscription stream
	stream := CountSubscriptionResolver(5)
	
	for val := range stream {
		fmt.Printf("Pushed to client: { \"data\": { \"count\": %d } }\n", val)
	}
	
	fmt.Println("Subscription closed.")
}
