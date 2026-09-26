package main

import (
	"context"
	"github.com/gin-gonic/gin"
	"go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	"go.opentelemetry.io/otel/sdk/trace"
)

func initTracer() *trace.TracerProvider {
	exporter, _ := stdouttrace.New(stdouttrace.WithPrettyPrint())
	tp := trace.NewTracerProvider(trace.WithBatcher(exporter))
	otel.SetTracerProvider(tp)
	return tp
}

func main() {
	tp := initTracer()
	defer tp.Shutdown(context.Background())

	r := gin.Default()
	r.Use(otelgin.Middleware("my-gin-service"))

	r.GET("/ping", func(c *gin.Context) {
		tracer := otel.Tracer("gin-server")
		_, span := tracer.Start(c.Request.Context(), "internal_work")
		defer span.End()
		
		c.JSON(200, gin.H{"message": "pong"})
	})

	r.Run(":8080")
}
