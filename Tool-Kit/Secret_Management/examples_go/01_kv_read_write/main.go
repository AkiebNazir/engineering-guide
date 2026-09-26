package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"github.com/hashicorp/vault/api"
)

func main() {
	config := api.DefaultConfig()
	client, err := api.NewClient(config)
	if err != nil {
		log.Fatalf("Unable to initialize Vault client: %v", err)
	}

	client.SetToken(os.Getenv("VAULT_TOKEN"))
	ctx := context.Background()
	secretData := map[string]interface{}{"api_key": "go-secret-123", "db_pass": "go-pass-456"}

	_, err = client.KVv2("secret").Put(ctx, "myapp/config", secretData)
	if err != nil {
		log.Fatalf("Unable to write secret: %v", err)
	}
	fmt.Println("Secret successfully written.")

	secret, err := client.KVv2("secret").Get(ctx, "myapp/config")
	if err != nil {
		log.Fatalf("Unable to read secret: %v", err)
	}
	fmt.Printf("Retrieved Secret: %v\n", secret.Data)
}
