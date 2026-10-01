package main

import (
	"log"
	"net/http"
)

func uploadHandler(w http.ResponseWriter, r *http.Request) {
	r.ParseMultipartForm(10 << 20) // 10 MB limit
	
	file, handler, err := r.FormFile("profile_pic")
	if err != nil {
		http.Error(w, "Error Retrieving File", http.StatusBadRequest)
		return
	}
	defer file.Close()
	
	log.Printf("Uploaded File: %+v, Size: %+v", handler.Filename, handler.Size)
	
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("File uploaded"))
}

func main() {
	http.HandleFunc("/upload", uploadHandler)
	http.ListenAndServe(":8080", nil)
}
