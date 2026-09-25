package main
import (
	"fmt"
	"net/http"
	"time"
)
func main() {
	srv := &http.Server{
		Addr:         ":8081",
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  15 * time.Second,
	}
	go srv.ListenAndServe()
	time.Sleep(100 * time.Millisecond)
	fmt.Println("OK")
}
