package main

import (
	"fmt"
	"log"

	"gonum.org/v1/gonum/graph/simple"
	"gonum.org/v1/gonum/graph/topo"
)

// TaskNode represents a task in our DAG, implementing graph.Node
type TaskNode struct {
	id   int64
	name string
}

func (n TaskNode) ID() int64 {
	return n.id
}

func main() {
	// Initialize a directed graph
	dag := simple.NewDirectedGraph()

	// Create nodes (Tasks)
	taskA := TaskNode{id: 1, name: "Task_A"}
	taskB := TaskNode{id: 2, name: "Task_B"}
	taskC := TaskNode{id: 3, name: "Task_C"}
	taskD := TaskNode{id: 4, name: "Task_D"}
	taskE := TaskNode{id: 5, name: "Task_E"}

	// Add nodes to the DAG
	dag.AddNode(taskA)
	dag.AddNode(taskB)
	dag.AddNode(taskC)
	dag.AddNode(taskD)
	dag.AddNode(taskE)

	// Define dependencies: A -> B, A -> C, B -> D, C -> D, D -> E
	dag.SetEdge(simple.Edge{F: taskA, T: taskB})
	dag.SetEdge(simple.Edge{F: taskA, T: taskC})
	dag.SetEdge(simple.Edge{F: taskB, T: taskD})
	dag.SetEdge(simple.Edge{F: taskC, T: taskD})
	dag.SetEdge(simple.Edge{F: taskD, T: taskE})

	fmt.Println("Attempting topological sort of the DAG...")

	// Perform topological sort using gonum's graph library
	sortedNodes, err := topo.Sort(dag)
	if err != nil {
		log.Fatalf("Failed to resolve DAG dependencies: %v", err)
	}

	fmt.Println("Execution Order:")
	for i, node := range sortedNodes {
		task := node.(TaskNode)
		if i > 0 {
			fmt.Print(" -> ")
		}
		fmt.Print(task.name)
	}
	fmt.Println()
}
