package main

import (
	"context"
	"fmt"
	"github.com/graph-gophers/dataloader"
)

// In a real application, this would query a database.
func loadPostsForUsers(ctx context.Context, keys dataloader.Keys) []*dataloader.Result {
	results := make([]*dataloader.Result, len(keys))
	
	// Simulated DB hit for multiple keys in ONE query
	fmt.Printf("Simulating SELECT * FROM posts WHERE user_id IN %v\n", keys)
	
	mockDB := map[string][]string{
		"user1": {"Post A", "Post B"},
		"user2": {"Post C"},
	}

	for i, key := range keys {
		userID := key.String()
		posts := mockDB[userID]
		results[i] = &dataloader.Result{Data: posts, Error: nil}
	}
	
	return results
}

func main() {
	// Initialize the dataloader
	postLoader := dataloader.NewBatchedLoader(loadPostsForUsers)
	
	// Simulate GraphQL resolver concurrently requesting posts for multiple users
	// Instead of 3 DB queries, the dataloader batches them into 1.
	ctx := context.Background()
	thunk1 := postLoader.Load(ctx, dataloader.StringKey("user1"))
	thunk2 := postLoader.Load(ctx, dataloader.StringKey("user2"))
	
	posts1, _ := thunk1()
	posts2, _ := thunk2()
	
	fmt.Printf("User 1 Posts: %v\n", posts1)
	fmt.Printf("User 2 Posts: %v\n", posts2)
}
