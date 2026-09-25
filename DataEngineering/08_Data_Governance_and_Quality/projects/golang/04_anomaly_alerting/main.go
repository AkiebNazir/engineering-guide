package main

import (
	"fmt"
	"math"
)

func detectAnomaly(val, mean, std float64, threshold float64) string {
	zScore := math.Abs((val - mean) / std)
	if zScore > threshold {
		return fmt.Sprintf("ALERT: Anomaly! Value %.2f is %.2f std devs away.", val, zScore)
	}
	return "Status Normal."
}

func main() {
	mean := 100.0
	std := 5.0
	fmt.Println(detectAnomaly(500.0, mean, std, 3.0)) // Spike
	fmt.Println(detectAnomaly(102.0, mean, std, 3.0)) // Normal
}
