package main
import (
	"encoding/base64"
	"fmt"
	"log"
	"os"
	"github.com/hashicorp/vault/api"
)
func main() {
	client, _ := api.NewClient(api.DefaultConfig())
	client.SetToken(os.Getenv("VAULT_TOKEN"))

	plaintext := []byte("Confidential Go Data")
	encodedPlaintext := base64.StdEncoding.EncodeToString(plaintext)

	encData := map[string]interface{}{"plaintext": encodedPlaintext}
	encResp, err := client.Logical().Write("transit/encrypt/my-app-key", encData)
	if err != nil { log.Fatalf("Encryption failed: %v", err) }
	
	ciphertext := encResp.Data["ciphertext"].(string)
	fmt.Printf("Ciphertext: %s\n", ciphertext)

	decData := map[string]interface{}{"ciphertext": ciphertext}
	decResp, err := client.Logical().Write("transit/decrypt/my-app-key", decData)
	
	decodedRaw, _ := base64.StdEncoding.DecodeString(decResp.Data["plaintext"].(string))
	fmt.Printf("Decrypted Data: %s\n", string(decodedRaw))
}
