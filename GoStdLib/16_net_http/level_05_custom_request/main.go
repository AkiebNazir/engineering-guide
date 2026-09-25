package main
import (
	"fmt"
	"net/http"
)
func main() {
	req, _ := http.NewRequest("GET", "https://example.com", nil)
	req.Header.Add("Authorization", "Bearer token")
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	fmt.Println("OK")
}
