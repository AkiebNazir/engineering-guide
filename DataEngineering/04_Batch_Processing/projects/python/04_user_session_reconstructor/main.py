import pandas as pd

def generate_events(filename="events.csv"):
    data = {
        "user_id": [1, 1, 1, 2, 2],
        "timestamp": [
            "2023-10-01 10:00:00",
            "2023-10-01 10:15:00",
            "2023-10-01 11:00:00",
            "2023-10-01 10:00:00",
            "2023-10-01 10:05:00",
        ],
        "page": ["/home", "/about", "/contact", "/home", "/products"]
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

def reconstruct_sessions(filename="events.csv", timeout_minutes=30):
    df = pd.read_csv(filename)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['user_id', 'timestamp'])
    
    df['time_diff'] = df.groupby('user_id')['timestamp'].diff()
    df['new_session'] = (df['time_diff'] > pd.Timedelta(minutes=timeout_minutes)) | df['time_diff'].isna()
    df['session_id'] = df.groupby('user_id')['new_session'].cumsum()
    
    print("Reconstructed Sessions:")
    print(df[['user_id', 'timestamp', 'page', 'session_id']])
    
if __name__ == "__main__":
    generate_events()
    reconstruct_sessions()
