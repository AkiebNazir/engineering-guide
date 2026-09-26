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

	secret, err := client.Logical().Read("aws/creds/my-s3-role")
	if err != nil || secret == nil { log.Fatalf("Unable to read AWS credentials: %v", err) }

	fmt.Println("Generated AWS Credentials:")
	fmt.Printf("Access Key: %s\n", secret.Data["access_key"])
	fmt.Printf("Secret Key: %s\n", secret.Data["secret_key"])
}
