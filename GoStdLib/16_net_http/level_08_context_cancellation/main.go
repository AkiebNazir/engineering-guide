package main
import (
	"context"
	"fmt"
	"net/http"
	"time"
)
func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()
	req, _ := http.NewRequestWithContext(ctx, "GET", "https://example.com", nil)
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	fmt.Println("OK")
}
