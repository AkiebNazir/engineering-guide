package main
import (
	"fmt"
	"net/http"
	"time"
)
func main() {
	t := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 100,
		IdleConnTimeout:     90 * time.Second,
	}
	client := &http.Client{Transport: t}
	_, err := client.Get("https://example.com")
	if err != nil {
		panic(err)
	}
	fmt.Println("OK")
}
