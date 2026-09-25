package main
import (
	"fmt"
	"net/http"
	"time"
)
func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "Hello")
	})
	go http.ListenAndServe(":8080", nil)
	time.Sleep(100 * time.Millisecond)
	fmt.Println("OK")
}
