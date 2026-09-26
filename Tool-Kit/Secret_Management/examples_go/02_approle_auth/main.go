package main
import (
	"fmt"
	"log"
	"os"
	"github.com/hashicorp/vault/api"
)
func main() {
	config := api.DefaultConfig()
	client, err := api.NewClient(config)
	if err != nil { log.Fatalf("Unable to initialize client: %v", err) }

	data := map[string]interface{}{
		"role_id":   os.Getenv("VAULT_ROLE_ID"),
		"secret_id": os.Getenv("VAULT_SECRET_ID"),
	}

	resp, err := client.Logical().Write("auth/approle/login", data)
	if err != nil { log.Fatalf("AppRole login failed: %v", err) }

	client.SetToken(resp.Auth.ClientToken)
	fmt.Println("Successfully authenticated via AppRole!")
}
