package main
import (
	"fmt"
	"log"
	"os"
	"github.com/hashicorp/vault/api"
)
func main() {
	client, _ := api.NewClient(api.DefaultConfig())
	client.SetToken(os.Getenv("VAULT_TOKEN"))

	secret, err := client.Logical().Read("database/creds/my-app-role")
	if err != nil || secret == nil { log.Fatalf("Unable to read dynamic DB credentials: %v", err) }

	fmt.Printf("Dynamic DB Username: %s\n", secret.Data["username"])
	fmt.Printf("Dynamic DB Password: %s\n", secret.Data["password"])
}
