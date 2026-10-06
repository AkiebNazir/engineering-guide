package main

import (
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"golang.org/x/time/rate"
)

// IP-based Rate Limiter
type IPLimiter struct {
	ips map[string]*rate.Limiter
	mu  *sync.RWMutex
	r   rate.Limit
	b   int
}

func NewIPLimiter(r rate.Limit, b int) *IPLimiter {
	return &IPLimiter{
		ips: make(map[string]*rate.Limiter),
		mu:  &sync.RWMutex{},
		r:   r,
		b:   b,
	}
}

func (i *IPLimiter) AddIP(ip string) *rate.Limiter {
	i.mu.Lock()
	defer i.mu.Unlock()

	limiter := rate.NewLimiter(i.r, i.b)
	i.ips[ip] = limiter
	return limiter
}

func (i *IPLimiter) GetLimiter(ip string) *rate.Limiter {
	i.mu.RLock()
	limiter, exists := i.ips[ip]
	i.mu.RUnlock()

	if !exists {
		return i.AddIP(ip)
	}
	return limiter
}

// RateLimitMiddleware enforces requests per second
func RateLimitMiddleware(limiter *IPLimiter) gin.HandlerFunc {
	return func(c *gin.Context) {
		clientIP := c.ClientIP()
		l := limiter.GetLimiter(clientIP)

		// Allow() consumes 1 token from the bucket
		if !l.Allow() {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"error": "Rate limit exceeded. Try again later.",
			})
			return
		}
		c.Next()
	}
}

func main() {
	r := gin.Default()

	// Allow 5 requests per second, with a maximum burst of 10
	limiter := NewIPLimiter(rate.Every(200*time.Millisecond), 10)

	r.Use(RateLimitMiddleware(limiter))

	r.GET("/api/data", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "Success!"})
	})

	log.Println("Rate limited API running on :8080...")
	r.Run(":8080")
}
