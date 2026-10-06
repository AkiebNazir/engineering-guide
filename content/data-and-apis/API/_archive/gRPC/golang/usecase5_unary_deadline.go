package main

import (
	"context"
	"log"
	"time"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type Task struct { TaskId string; Payload string }
type TaskResult struct { TaskId string; Status string }

type server struct{}

func (s *server) ProcessTask(ctx context.Context, req *Task) (*TaskResult, error) {
	log.Printf("Starting task: %s", req.TaskId)
	
	done := make(chan *TaskResult, 1)
	
	go func() {
		time.Sleep(3 * time.Second)
		done <- &TaskResult{TaskId: req.TaskId, Status: "COMPLETED"}
	}()
	
	select {
	case <-ctx.Done(): 
		log.Printf("Task %s aborted: %v", req.TaskId, ctx.Err())
		return nil, status.Error(codes.DeadlineExceeded, "Task timed out")
	case res := <-done:
		log.Printf("Task %s finished", req.TaskId)
		return res, nil
	}
}

func main() {}
