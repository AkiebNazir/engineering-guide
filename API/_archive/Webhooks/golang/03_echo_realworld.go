// REAL-WORLD EXAMPLE: Echo (External 2)
// Demonstrates: Error handling and raw body reading
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"io"
	"log"
	"net/http"

	"github.com/labstack/echo/v4"
)

func main() {
	e := echo.New()
	
	e.POST("/webhooks/stripe", func(c echo.Context) error {
		payload, err := io.ReadAll(c.Request().Body)
		if err != nil {
			return c.JSON(http.StatusBadRequest, map[string]string{"error": "Cannot read body"})
		}
		
		sig := c.Request().Header.Get("Stripe-Signature")

		mac := hmac.New(sha256.New, []byte("whsec_my_super_secret"))
		mac.Write(payload)
		expected := hex.EncodeToString(mac.Sum(nil))

		if !hmac.Equal([]byte(expected), []byte(sig)) {
			return c.JSON(http.StatusUnauthorized, map[string]string{"error": "Invalid signature"})
		}
		
		log.Println("Verified webhook payload:", string(payload))
		return c.JSON(http.StatusOK, map[string]string{"status": "success"})
	})
	
	e.Start(":8080")
}
