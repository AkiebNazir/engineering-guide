// REAL-WORLD EXAMPLE: Echo (External 2)
// Demonstrates: Context injection, Centralized Error Handling, JWT Auth Simulation, Clean Architecture Routing
package main

import (
	"fmt"
	"net/http"
	"strconv"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

type Payment struct {
	ID     string  `json:"id"`
	Amount float64 `json:"amount"`
	Status string  `json:"status"`
}

type PaymentRequest struct {
	Amount float64 `json:"amount"`
}

type CustomContext struct {
	echo.Context
	DB map[string]*Payment
}

// CustomMiddleware injects our mock DB into the context
func DBContextMiddleware(db map[string]*Payment) echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			cc := &CustomContext{c, db}
			return next(cc)
		}
	}
}

func createPayment(c echo.Context) error {
	cc := c.(*CustomContext) // Type assert to our custom context
	
	req := new(PaymentRequest)
	if err := cc.Bind(req); err != nil {
		return echo.NewHTTPError(http.StatusBadRequest, "Invalid JSON format")
	}
	
	if req.Amount <= 0 {
		return echo.NewHTTPError(http.StatusBadRequest, "Amount must be greater than 0")
	}

	id := strconv.Itoa(len(cc.DB) + 1)
	payment := &Payment{
		ID:     id,
		Amount: req.Amount,
		Status: "PROCESSING",
	}
	cc.DB[id] = payment

	return cc.JSON(http.StatusCreated, payment)
}

func getPayment(c echo.Context) error {
	cc := c.(*CustomContext)
	id := cc.Param("id")
	
	if payment, exists := cc.DB[id]; exists {
		return cc.JSON(http.StatusOK, payment)
	}
	return echo.NewHTTPError(http.StatusNotFound, fmt.Sprintf("Payment %s not found", id))
}

func main() {
	e := echo.New()
	
	// Middleware
	e.Use(middleware.Logger())
	e.Use(middleware.Recover())
	
	mockDB := make(map[string]*Payment)
	e.Use(DBContextMiddleware(mockDB))

	// Centralized Error Handler (masks internal errors in prod)
	e.HTTPErrorHandler = func(err error, c echo.Context) {
		code := http.StatusInternalServerError
		msg := "Internal Server Error"
		if he, ok := err.(*echo.HTTPError); ok {
			code = he.Code
			msg = fmt.Sprintf("%v", he.Message)
		}
		c.JSON(code, map[string]string{"error": msg})
	}

	// Routes
	g := e.Group("/payments")
	g.Use(middleware.KeyAuth(func(key string, c echo.Context) (bool, error) {
		return key == "valid-key", nil // Simple Auth
	}))
	
	g.POST("", createPayment)
	g.GET("/:id", getPayment)

	e.Logger.Fatal(e.Start(":8080"))
}
