package main

import (
	"log"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

// --- Models ---
type Article struct {
	ID      int    `json:"id"`
	Title   string `json:"title" binding:"required"` // binding enforces validation
	Content string `json:"content" binding:"required"`
	Author  string `json:"author"`
}

// Mock Database
var db = make(map[int]Article)
var nextID = 1

// --- Middlewares ---

// LoggerMiddleware logs every request (Real world: structured logging, latency tracking)
func LoggerMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		log.Printf("[%s] %s", c.Request.Method, c.Request.URL.Path)
		c.Next() // Pass control to the next handler
	}
}

// AuthMiddleware checks for a Bearer token (Real world: JWT Validation)
func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		token := c.GetHeader("Authorization")
		if token != "Bearer secret-production-token" {
			// Abort stops the chain and returns an error immediately
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized access"})
			return
		}
		// Set context variable for downstream handlers
		c.Set("user_id", "admin_99")
		c.Next()
	}
}

// --- Handlers ---

// CreateArticle: Demonstrates JSON Body Binding
func CreateArticle(c *gin.Context) {
	var newArticle Article
	// BindJSON automatically returns 400 Bad Request if fields are missing/invalid
	if err := c.ShouldBindJSON(&newArticle); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	
	newArticle.ID = nextID
	nextID++
	
	// Read from context (set by AuthMiddleware)
	author, _ := c.Get("user_id")
	newArticle.Author = author.(string)
	
	db[newArticle.ID] = newArticle
	
	c.JSON(http.StatusCreated, gin.H{"data": newArticle})
}

// GetArticles: Demonstrates Query Parameters (?limit=10&sort=asc)
func GetArticles(c *gin.Context) {
	// Query param with a default value
	limitStr := c.DefaultQuery("limit", "10")
	limit, _ := strconv.Atoi(limitStr)
	
	var result []Article
	count := 0
	for _, article := range db {
		if count >= limit { break }
		result = append(result, article)
		count++
	}
	
	c.JSON(http.StatusOK, gin.H{"data": result, "limit_applied": limit})
}

// GetArticleByID: Demonstrates Path Parameters (/articles/:id)
func GetArticleByID(c *gin.Context) {
	idStr := c.Param("id") // Extract path param
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID format"})
		return
	}
	
	article, exists := db[id]
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "Article not found"})
		return
	}
	
	c.JSON(http.StatusOK, gin.H{"data": article})
}

// UpdateArticle: Demonstrates PUT (Complete replacement) vs PATCH (Partial)
func UpdateArticle(c *gin.Context) {
	idStr := c.Param("id")
	id, _ := strconv.Atoi(idStr)
	
	if _, exists := db[id]; !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "Article not found"})
		return
	}
	
	var updatedData Article
	if err := c.ShouldBindJSON(&updatedData); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	
	updatedData.ID = id // Ensure ID isn't overridden
	db[id] = updatedData
	
	c.JSON(http.StatusOK, gin.H{"data": db[id]})
}

func DeleteArticle(c *gin.Context) {
	idStr := c.Param("id")
	id, _ := strconv.Atoi(idStr)
	
	delete(db, id)
	c.Status(http.StatusNoContent) // 204 No Content
}

func main() {
	// Initialize Gin router
	r := gin.New()
	
	// Apply Global Middleware
	r.Use(gin.Recovery()) // Recovers from panics
	r.Use(LoggerMiddleware())

	// Public Routes (No Auth required)
	r.GET("/ping", func(c *gin.Context) { c.JSON(200, gin.H{"message": "pong"}) })

	// Protected Routes Group
	v1 := r.Group("/api/v1")
	v1.Use(AuthMiddleware()) 
	{
		// /api/v1/articles
		v1.POST("/articles", CreateArticle)          // Body binding
		v1.GET("/articles", GetArticles)             // Query params
		v1.GET("/articles/:id", GetArticleByID)      // Path params
		v1.PUT("/articles/:id", UpdateArticle)       // Path + Body
		v1.DELETE("/articles/:id", DeleteArticle)    // Path params
	}

	log.Println("Server running on port 8080...")
	r.Run(":8080")
}
