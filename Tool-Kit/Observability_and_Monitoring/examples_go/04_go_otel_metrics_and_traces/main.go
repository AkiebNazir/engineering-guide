package main

import (
	"context"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
)

func main() {
	ctx := context.Background()
	res := resource.Default()

	tp := sdktrace.NewTracerProvider(sdktrace.WithResource(res))
	otel.SetTracerProvider(tp)

	mp := sdkmetric.NewMeterProvider(sdkmetric.WithResource(res))
	otel.SetMeterProvider(mp)

	tracer := otel.Tracer("example/trace")
	meter := otel.Meter("example/metric")

	counter, _ := meter.Int64Counter("jobs.completed", metric.WithDescription("Completed jobs"))

	ctx, span := tracer.Start(ctx, "job.process")
	counter.Add(ctx, 1)
	span.End()
}
