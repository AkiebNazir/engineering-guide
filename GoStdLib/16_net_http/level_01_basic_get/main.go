package main
import (
	"fmt"
	"io"
	"net/http"
)
func main() {
	resp, err := http.Get("https://example.com")
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if len(body) > 0 {
		fmt.Println("OK")
	}
}
