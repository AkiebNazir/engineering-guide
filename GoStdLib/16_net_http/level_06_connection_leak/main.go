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
	// Missing read to EOF and close causes leak
	io.Copy(io.Discard, resp.Body)
	resp.Body.Close()
	fmt.Println("OK")
}
