package main

import (
	"fmt"
	"strings"
)

type Node struct {
	Name       string
	Downstream []*Node
}

func (n *Node) PrintLineage(level int) {
	fmt.Printf("%s-> %s
", strings.Repeat("  ", level), n.Name)
	for _, child := range n.Downstream {
		child.PrintLineage(level + 1)
	}
}

func main() {
	raw := &Node{Name: "raw_transactions"}
	stg := &Node{Name: "stg_transactions"}
	fct := &Node{Name: "fct_daily_sales"}

	raw.Downstream = append(raw.Downstream, stg)
	stg.Downstream = append(stg.Downstream, fct)

	fmt.Println("Data Lineage Graph:")
	raw.PrintLineage(0)
}
