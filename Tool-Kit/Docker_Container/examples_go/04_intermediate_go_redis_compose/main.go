package main
import (
    "context"
    "fmt"
    "net/http"
    "github.com/redis/go-redis/v9"
)
var ctx = context.Background()
func main() {
    rdb := redis.NewClient(&redis.Options{
        Addr: "redis:6379", // DNS resolution via Docker Compose network
    })
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        val, err := rdb.Incr(ctx, "hits").Result()
        if err != nil {
            http.Error(w, err.Error(), 500)
            return
        }
        fmt.Fprintf(w, "Hits: %d\n", val)
    })
    http.ListenAndServe(":8080", nil)
}
