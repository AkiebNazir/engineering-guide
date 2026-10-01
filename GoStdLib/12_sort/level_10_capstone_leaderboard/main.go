/*
LEVEL 10 (capstone) - a leaderboard: multi-key stable sort plus a rank lookup

This wires together levels 1-9:
  - a multi-key comparator (score desc, then name asc as tiebreak) (level 3)
  - sort.SliceStable so equal-score players keep their submission order
    among further ties, matching level 9's lesson about picking Stable
    on purpose rather than by accident
  - sort.Search to answer "how many players score higher than X" over the
    now-descending-sorted scores (levels 4 and 7's binary-search pattern)
  - sort.IntsAreSorted as a sanity check on the extracted score column (1)

Run: go run ./GoStdLib/12_sort/level_10_capstone_leaderboard
*/

package main

import (
	"fmt"
	"sort"
)

type entry struct {
	name  string
	score int
}

// rank returns how many entries strictly outscore `score` in a leaderboard
// already sorted descending by score - i.e. the 0-based rank a new score of
// `score` would land at.
func rank(board []entry, score int) int {
	return sort.Search(len(board), func(i int) bool { return board[i].score <= score })
}

func main() {
	board := []entry{
		{"nova", 88}, {"pico", 95}, {"kai", 88},
		{"lux", 71}, {"zed", 95}, {"mira", 88},
	}

	sort.SliceStable(board, func(i, j int) bool {
		if board[i].score != board[j].score {
			return board[i].score > board[j].score // higher score first
		}
		return board[i].name < board[j].name // tiebreak: alphabetical
	})

	want := []entry{
		{"pico", 95}, {"zed", 95},
		{"kai", 88}, {"mira", 88}, {"nova", 88},
		{"lux", 71},
	}
	if len(board) != len(want) {
		panic(fmt.Sprintf("length mismatch: got %d, want %d", len(board), len(want)))
	}
	for i := range want {
		if board[i] != want[i] {
			panic(fmt.Sprintf("index %d: got %+v, want %+v (board=%v)", i, board[i], want[i], board))
		}
	}

	scores := make([]int, len(board))
	for i, e := range board {
		scores[i] = e.score
	}
	descending := true
	for i := 1; i < len(scores); i++ {
		if scores[i] > scores[i-1] {
			descending = false
		}
	}
	if !descending {
		panic(fmt.Sprintf("scores should be non-increasing: %v", scores))
	}
	if sort.IntsAreSorted(scores) && len(scores) > 1 && scores[0] != scores[len(scores)-1] {
		panic("scores should NOT be ascending-sorted (they are descending)")
	}

	if r := rank(board, 90); r != 2 {
		panic(fmt.Sprintf("rank(90) = %d, want 2 (pico and zed outscore it)", r))
	}
	if r := rank(board, 88); r != 2 {
		panic(fmt.Sprintf("rank(88) = %d, want 2 (only the two 95s strictly outscore it)", r))
	}
	if r := rank(board, 100); r != 0 {
		panic(fmt.Sprintf("rank(100) = %d, want 0 (nobody outscores it)", r))
	}
	if r := rank(board, 0); r != len(board) {
		panic(fmt.Sprintf("rank(0) = %d, want %d (everybody outscores it)", r, len(board)))
	}

	fmt.Println("leaderboard:")
	for i, e := range board {
		fmt.Printf("  %d. %-5s %d\n", i+1, e.name, e.score)
	}
	fmt.Printf("a new score of 90 would rank at position %d\n", rank(board, 90)+1)
	fmt.Println("OK")
}
