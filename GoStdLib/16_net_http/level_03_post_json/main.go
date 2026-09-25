package main
import (
	"bytes"
	"fmt"
	"net/http"
)
func main() {
	data := []byte(`{"key":"value"}`)
	resp, err := http.Post("https://example.com", "application/json", bytes.NewBuffer(data))
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	fmt.Println("OK")
}
