package main

import "fmt"

type Node struct {
	Value int
	Next  *Node
}

type LinkList struct {
	Root *Node
}

func (l *LinkList) insert(value int) {
	if l.Root == nil {
		l.Root = &Node{Value: value}
		return
	}
	head := l.Root
	for head.Next != nil {
		head = head.Next
	}
	head.Next = &Node{Value: value}
}

func (l *LinkList) display() {
	if l.Root == nil {
		fmt.Println("empty link list...!")
		return
	}
	linkList := []int{}
	head := l.Root
	for head != nil {
		linkList = append(linkList, head.Value)
		head = head.Next
	}
	fmt.Println("Link List: ", linkList)
}

func (l *LinkList) delete(value int) {
	if l.Root == nil {
		fmt.Println("delete on empty link list...!")
		return
	}
	head := l.Root
	if head.Value == value {
		l.Root = head.Next
		return
	}
	for head.Next != nil {
		if head.Next.Value == value {
			head.Next = head.Next.Next
			return
		}
		head = head.Next
	}
}

func main() {
	linkList := LinkList{}
	linkList.insert(20)
	linkList.insert(30)
	linkList.insert(40)
	linkList.insert(50)

	linkList.display()
	linkList.delete(30)
	linkList.display()
}
