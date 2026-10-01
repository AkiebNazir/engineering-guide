// REAL-WORLD EXAMPLE: Gin (External 1)
// Demonstrates: Webhook verification via Middleware, JSON parsing
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"io"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
)

var webhookSecret = []byte("whsec_my_super_secret")

func VerifySignatureMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		payload, _ := io.ReadAll(c.Request.Body)
		sig := c.GetHeader("Stripe-Signature")

		mac := hmac.New(sha256.New, webhookSecret)
		mac.Write(payload)
		expected := hex.EncodeToString(mac.Sum(nil))

		if !hmac.Equal([]byte(expected), []byte(sig)) {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid signature"})
			return
		}
		
		// Put payload back into context so next handler can parse JSON
		c.Set("raw_payload", payload)
		c.Next()
	}
}

func main() {
	r := gin.Default()
	
	r.POST("/webhooks/stripe", VerifySignatureMiddleware(), func(c *gin.Context) {
		// Just acknowledge receipt for this example
		log.Println("Valid Webhook Received!")
		c.JSON(http.StatusOK, gin.H{"status": "success"})
	})
	
	r.Run(":8080")
}
