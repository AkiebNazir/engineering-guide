import os
import numpy as np
from sklearn.ensemble import IsolationForest
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def detect_anomalies(data):
    """
    Uses IsolationForest to detect anomalies in a dataset.
    Isolation Forest is standard for outlier detection in high-dimensional data.
    """
    # Reshape data for sklearn (requires 2D array)
    X = np.array(data).reshape(-1, 1)
    
    # Initialize and fit the model
    # contamination indicates the expected proportion of outliers (e.g., 5%)
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)
    
    # Predict anomalies: -1 for anomaly, 1 for normal
    predictions = model.predict(X)
    
    anomalies = []
    for i, pred in enumerate(predictions):
        if pred == -1:
            anomalies.append((i, data[i]))
            
    return anomalies

def send_slack_alert(anomalies):
    """
    Sends an alert to a Slack channel using slack_sdk.
    """
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    if not slack_token:
        print("SLACK_BOT_TOKEN environment variable not set. Skipping real Slack alert.")
        # Fallback to local logging
        for idx, val in anomalies:
            print(f"[MOCK ALERT] Anomaly detected at index {idx} with value {val}.")
        return

    client = WebClient(token=slack_token)
    channel_id = "#data-engineering-alerts"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚨 Data Anomaly Alert 🚨"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Detected *{len(anomalies)}* anomalies in the recent data pipeline run."
            }
        }
    ]
    
    for idx, val in anomalies:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"• Index: `{idx}`, Value: `{val}`"
            }
        })
        
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text="Data Anomaly Alert"
        )
        print(f"Alert successfully sent to {channel_id}.")
    except SlackApiError as e:
        print(f"Error sending message to Slack: {e.response['error']}")

def main():
    print("Fetching recent pipeline metrics...")
    # Simulate a stream of data (e.g., row counts, latency, or total sales)
    # Most values are around 100, but 500 is a clear anomaly.
    historical_data = [100, 105, 95, 110, 90, 102, 98, 101, 104, 96, 500, 99, 100]
    
    print("Running Isolation Forest Anomaly Detection...")
    anomalies = detect_anomalies(historical_data)
    
    if anomalies:
        print(f"Found {len(anomalies)} anomalies. Triggering alerts...")
        send_slack_alert(anomalies)
    else:
        print("No anomalies detected. Pipeline is healthy.")

if __name__ == "__main__":
    main()
