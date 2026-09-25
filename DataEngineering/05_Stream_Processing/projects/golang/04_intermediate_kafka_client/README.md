# 04 Intermediate Kafka Client

Demonstrates how to produce and consume messages to/from an Apache Kafka topic using the `segmentio/kafka-go` library.

## Prerequisites
You need a running instance of Kafka on `localhost:9092`.

## Usage
Initialize the module and download dependencies:
```bash
go mod init kafka_client
go get github.com/segmentio/kafka-go
```

Run the producer and consumer in separate terminal windows:
```bash
go run producer.go
```
```bash
go run consumer.go
```
