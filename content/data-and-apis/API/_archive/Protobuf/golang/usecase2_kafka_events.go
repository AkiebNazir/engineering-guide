package main

import (
	"log"
	"github.com/confluentinc/confluent-kafka-go/kafka"
	// "google.golang.org/protobuf/proto"
)

type User struct { Id int32; Name string; Email string }

func publishEvent(p *kafka.Producer, user *User) {
	// binaryPayload, _ := proto.Marshal(user)
	binaryPayload := []byte("mock binary payload")
	
	topic := "user_events"
	err := p.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
		Value:          binaryPayload,
	}, nil)
	
	if err != nil {
		log.Println("Error producing message:", err)
	} else {
		log.Println("Produced protobuf message to Kafka")
	}
}

func main() {}
