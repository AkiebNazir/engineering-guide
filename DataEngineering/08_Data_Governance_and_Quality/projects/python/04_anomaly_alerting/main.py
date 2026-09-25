import numpy as np

def detect_anomaly(current_value, historical_mean, historical_std, threshold=3):
    z_score = abs((current_value - historical_mean) / historical_std)
    if z_score > threshold:
        return f"ALERT: Anomaly detected! Value {current_value} is {z_score:.2f} std devs away from mean."
    return "Status Normal."

historical_data = [100, 105, 95, 110, 90, 102]
mean = np.mean(historical_data)
std = np.std(historical_data)

print(detect_anomaly(500, mean, std))  # Sudden spike
print(detect_anomaly(100, mean, std))  # Normal
