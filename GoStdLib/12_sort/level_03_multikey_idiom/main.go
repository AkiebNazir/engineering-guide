/*
LEVEL 03 (idiom) - multi-key sorting with a single closure

You will learn
  - the realistic idiom for "sort by A, and within equal A, by B": one
    closure that checks the primary key first and only consults the
    secondary key when the primary keys are equal
  - this needs no extra type or package help - it is just an if/else inside
    the Less closure sort.Slice already takes

Run: go run ./GoStdLib/12_sort/level_03_multikey_idiom
*/

package main

import (
	"fmt"
	"sort"
)

type student struct {
	grade int
	name  string
}

func main() {
	students := []student{
		{grade: 90, name: "Ines"},
		{grade: 85, name: "Marco"},
		{grade: 90, name: "Ana"},
		{grade: 85, name: "Bilal"},
		{grade: 90, name: "Chen"},
	}

	// Primary key: grade, descending (best first). Secondary key, used only
	// when grades tie: name, ascending.
	sort.Slice(students, func(i, j int) bool {
		if students[i].grade != students[j].grade {
			return students[i].grade > students[j].grade
		}
		return students[i].name < students[j].name
	})

	want := []student{
		{90, "Ana"}, {90, "Chen"}, {90, "Ines"},
		{85, "Bilal"}, {85, "Marco"},
	}
	if len(students) != len(want) {
		panic(fmt.Sprintf("length mismatch: got %d, want %d", len(students), len(want)))
	}
	for i := range want {
		if students[i] != want[i] {
			panic(fmt.Sprintf("index %d: got %+v, want %+v", i, students[i], want[i]))
		}
	}

	fmt.Printf("ranked: %v\n", students)
	fmt.Println("OK")
}
