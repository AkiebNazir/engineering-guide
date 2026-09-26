package main

import (
	"fmt"
	"log"
	"math"
	"os"

	"github.com/slack-go/slack"
)

// calculateStats computes the mean and standard deviation of a dataset
func calculateStats(data []float64) (mean float64, stddev float64) {
	if len(data) == 0 {
		return 0, 0
	}
	var sum float64
	for _, v := range data {
		sum += v
	}
	mean = sum / float64(len(data))

	var varianceSum float64
	for _, v := range data {
		varianceSum += math.Pow(v-mean, 2)
	}
	variance := varianceSum / float64(len(data))
	stddev = math.Sqrt(variance)
	return mean, stddev
}

// detectAnomalies uses Z-Score to identify anomalies.
// A Z-Score threshold of 3 is typical in statistical quality control.
func detectAnomalies(data []float64, threshold float64) []int {
	mean, stddev := calculateStats(data)
	var anomalies []int

	for i, val := range data {
		zScore := math.Abs((val - mean) / stddev)
		if zScore > threshold {
			anomalies = append(anomalies, i)
		}
	}
	return anomalies
}

// sendSlackAlert pushes a notification to a Slack channel
func sendSlackAlert(data []float64, anomalies []int) {
	token := os.Getenv("SLACK_BOT_TOKEN")
	if token == "" {
		fmt.Println("SLACK_BOT_TOKEN environment variable not set. Skipping real Slack alert.")
		for _, idx := range anomalies {
			fmt.Printf("[MOCK ALERT] Anomaly detected at index %d (value: %.2f)\n", idx, data[idx])
		}
		return
	}

	api := slack.New(token)
	channelID := "#data-engineering-alerts" // Typically injected via config

	var blocks []slack.Block

	headerText := slack.NewTextBlockObject("plain_text", "🚨 Data Anomaly Alert 🚨", false, false)
	headerBlock := slack.NewHeaderBlock(headerText)
	blocks = append(blocks, headerBlock)

	msgText := slack.NewTextBlockObject("mrkdwn", fmt.Sprintf("Detected *%d* anomalies in recent metrics.", len(anomalies)), false, false)
	sectionBlock := slack.NewSectionBlock(msgText, nil, nil)
	blocks = append(blocks, sectionBlock)

	for _, idx := range anomalies {
		details := slack.NewTextBlockObject("mrkdwn", fmt.Sprintf("• Index: `%d`, Value: `%.2f`", idx, data[idx]), false, false)
		blocks = append(blocks, slack.NewSectionBlock(details, nil, nil))
	}

	_, _, err := api.PostMessage(
		channelID,
		slack.MsgOptionBlocks(blocks...),
		slack.MsgOptionText("Data Anomaly Alert", false),
	)
	if err != nil {
		log.Printf("Error sending Slack message: %v\n", err)
	} else {
		fmt.Printf("Alert successfully sent to %s\n", channelID)
	}
}

func main() {
	fmt.Println("Fetching recent pipeline metrics...")
	// Simulated metrics (e.g., number of failed records per minute)
	metrics := []float64{10, 12, 11, 9, 13, 10, 11, 100, 12, 10, 9}

	fmt.Println("Running Z-Score Anomaly Detection...")
	// Use 2.5 standard deviations as the threshold
	anomalies := detectAnomalies(metrics, 2.5)

	if len(anomalies) > 0 {
		fmt.Printf("Found %d anomalies. Triggering alerts...\n", len(anomalies))
		sendSlackAlert(metrics, anomalies)
	} else {
		fmt.Println("No anomalies detected. Pipeline is healthy.")
	}
}
