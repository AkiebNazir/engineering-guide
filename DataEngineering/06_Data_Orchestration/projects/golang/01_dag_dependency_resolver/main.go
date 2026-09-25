package main

import (
	"fmt"
	"strings"
)

func topologicalSort(dag map[string][]string) ([]string, error) {
	inDegree := make(map[string]int)
	for u, neighbors := range dag {
		if _, exists := inDegree[u]; !exists {
			inDegree[u] = 0
		}
		for _, v := range neighbors {
			inDegree[v]++
		}
	}

	var queue []string
	for u, degree := range inDegree {
		if degree == 0 {
			queue = append(queue, u)
		}
	}

	var order []string
	for len(queue) > 0 {
		u := queue[0]
		queue = queue[1:]
		order = append(order, u)

		for _, v := range dag[u] {
			inDegree[v]--
			if inDegree[v] == 0 {
				queue = append(queue, v)
			}
		}
	}

	if len(order) == len(inDegree) {
		return order, nil
	}
	return nil, fmt.Errorf("graph has a cycle")
}

func main() {
	dag := map[string][]string{
		"A": {"B", "C"},
		"B": {"D"},
		"C": {"D"},
		"D": {"E"},
		"E": {},
	}

	fmt.Println("DAG:")
	for k, v := range dag {
		fmt.Printf("  %s -> %v\n", k, v)
	}

	fmt.Println("\nExecution Order:")
	order, err := topologicalSort(dag)
	if err != nil {
		fmt.Println("Error:", err)
	} else {
		fmt.Println(strings.Join(order, " -> "))
	}
}
