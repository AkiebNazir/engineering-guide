package main
import (
	"fmt"
	"net/http"
	"time"
)
func main() {
	client := &http.Client{Timeout: 1 * time.Second}
	_, err := client.Get("https://example.com")
	if err != nil {
		panic(err)
	}
	fmt.Println("OK")
}
