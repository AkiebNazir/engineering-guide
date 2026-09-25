package main
import (
    "io/ioutil"
    "net/http"
    "os"
)
func main() {
    userServiceURL := os.Getenv("USER_SERVICE_URL")
    http.HandleFunc("/api/user", func(w http.ResponseWriter, r *http.Request) {
        resp, err := http.Get(userServiceURL + "/user")
        if err != nil {
            http.Error(w, "User service unavailable", 500)
            return
        }
        defer resp.Body.Close()
        body, _ := ioutil.ReadAll(resp.Body)
        w.Write(body)
    })
    http.ListenAndServe(":8080", nil)
}
