package main
import (
    "fmt"
    "net/http"
    "os"
)
func main() {
    dsn := os.Getenv("DB_DSN")
    http.HandleFunc("/user", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "User details fetched from DB: %s", dsn)
    })
    http.ListenAndServe(":9090", nil)
}
