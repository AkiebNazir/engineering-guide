// REAL-WORLD EXAMPLE: Gin (External 1)
// Demonstrates: Struct Validation, Middleware (Logger/Auth), Grouping, Custom Error Responses
package main

import (
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

// Request payload with strict validation tags
type CreateProductReq struct {
	Name  string  `json:"name" binding:"required,min=3"`
	Price float64 `json:"price" binding:"required,gt=0"`
}

type Product struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Price     float64   `json:"price"`
	CreatedAt time.Time `json:"created_at"`
}

var db = make(map[string]Product)

// AuthMiddleware simulates a real-world API key check
func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		apiKey := c.GetHeader("X-API-KEY")
		if apiKey != "supersecret" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized access"})
			return
		}
		c.Next() // Proceed to the handler
	}
}

func main() {
	// Disable console color, set release mode in production
	// gin.SetMode(gin.ReleaseMode)
	
	r := gin.New()
	
	// Global middleware
	r.Use(gin.Logger())
	r.Use(gin.Recovery())

	// API v1 Group with Auth Middleware
	v1 := r.Group("/api/v1")
	v1.Use(AuthMiddleware())
	{
		v1.POST("/products", func(c *gin.Context) {
			var req CreateProductReq
			if err := c.ShouldBindJSON(&req); err != nil {
				// Returns 400 with validation details
				c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
				return
			}
			
			id := strconv.Itoa(len(db) + 1)
			product := Product{
				ID:        id,
				Name:      req.Name,
				Price:     req.Price,
				CreatedAt: time.Now(),
			}
			db[id] = product
			
			c.JSON(http.StatusCreated, product)
		})

		v1.GET("/products/:id", func(c *gin.Context) {
			id := c.Param("id")
			if product, exists := db[id]; exists {
				c.JSON(http.StatusOK, product)
			} else {
				c.JSON(http.StatusNotFound, gin.H{"error": "Product not found"})
			}
		})
	}

	log.Println("Gin server running on :8080")
	r.Run(":8080")
}
