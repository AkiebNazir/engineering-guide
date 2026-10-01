# Day 55: Phase 2 Mid-Review & Time Series

Welcome to Day 55. We have reached a monumental milestone. You have mastered Convolutions, Sequence Models, Attention, Word Embeddings, and Speech Recognition. 
Today, we tie the entire NLP pipeline together, and then we apply our Sequence Models to the most lucrative domain in data science: **Financial Time Series Forecasting**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Complete NLP Pipeline Review
Every modern NLP system follows this exact mathematical pipeline:
1. **Raw Text:** `"I love AI!"`
2. **Tokenization (Day 49):** Split into subwords: `["I", "lo", "ve", "AI", "!"]`
3. **Vocabulary Lookup:** Convert to IDs: `[12, 456, 89, 2, 9]`
4. **Embeddings (Day 48):** Convert IDs to 300D spatial coordinates.
5. **Contextualization (Day 44):** Pass through a BiLSTM to mix the meaning of the words together.
6. **Attention (Day 51):** Extract the single most important vector.
7. **Classification:** Pass through an `nn.Linear` layer to predict Sentiment!

### 2. Time Series Fundamentals
A Time Series is just a sequence of numbers (e.g., Apple Stock prices every minute, or Server CPU load every hour). Because it is a sequence, we can use our NLP Sequence Models (LSTMs, 1D CNNs) to predict the future!
- **Stationarity:** A Time Series is "Stationary" if its mean and variance do not change over time. You cannot mathematically forecast a stock if it has a massive permanent upward trend. You must **Difference** the data (predicting the *change* in price, rather than the absolute price) to make it stationary before feeding it to the AI.
- **Autocorrelation:** How much does yesterday's data affect today's data? If it rains today, the probability of it raining tomorrow is mathematically higher. 

### 3. Classic Models vs Neural Models
- **ARIMA:** The classic statistical model. It uses explicit math to model the Autoregression (AR) and the Moving Average (MA) of the data. Highly interpretable, but struggles with complex, non-linear patterns.
- **LSTM / 1D CNN:** Neural models don't care about classic statistics. They blindly look at the past 30 days of data and learn complex non-linear patterns to predict day 31.

### 4. The Fatal Mistake: Temporal Data Splitting
If you are training an AI to predict cats and dogs, you use `train_test_split` to randomly shuffle the data.
**NEVER randomly shuffle Time Series data!**
If you shuffle stock data, you might accidentally put Friday's price in the Training set, and Thursday's price in the Test set. The AI will literally look into the future to predict the past. This is called **Look-Ahead Bias**.
You must use **Walk-Forward Validation** (train on Jan-March, test on April. Train on Jan-April, test on May).

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a PyTorch Time Series Forecaster using an LSTM. We will properly format a rolling window of historical data to predict the future.

Create a file named `time_series_lstm.py`:

```python
import torch
import torch.nn as nn

def create_rolling_windows(data_sequence, window_size):
    """
    Converts a flat time series into (Input, Target) pairs.
    If window_size = 3:
    Input: Days [1, 2, 3] -> Target: Day 4
    Input: Days [2, 3, 4] -> Target: Day 5
    """
    inputs = []
    targets = []
    
    # We stop exactly 'window_size' steps before the end
    for i in range(len(data_sequence) - window_size):
        x = data_sequence[i : i + window_size]
        y = data_sequence[i + window_size]
        inputs.append(x)
        targets.append(y)
        
    return torch.tensor(inputs), torch.tensor(targets)

class TimeSeriesLSTM(nn.Module):
    """
    A Neural Forecaster that looks at the past N days to predict tomorrow.
    """
    def __init__(self, input_size, hidden_size):
        super().__init__()
        
        # input_size = 1 (Because stock price is just 1 number per day)
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        
        # Predict the single continuous value for tomorrow
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x shape: [Batch, Window_Size, 1]
        
        # lstm_out shape: [Batch, Window_Size, Hidden_Size]
        lstm_out, _ = self.lstm(x)
        
        # We only care about the LSTM's output at the VERY LAST timestep!
        # Grab the last timestep: [Batch, Hidden_Size]
        last_time_step = lstm_out[:, -1, :]
        
        # Predict the future value: [Batch, 1]
        prediction = self.fc(last_time_step)
        
        return prediction

def test_forecaster():
    print("--- RUNNING TIME SERIES FORECASTER ---")
    
    # 1. Simulate 100 days of stock prices (e.g., a sine wave pattern)
    import math
    raw_data = [math.sin(i * 0.1) for i in range(100)]
    
    # 2. Create the Rolling Windows
    WINDOW_SIZE = 10 # Look at the past 10 days
    X, y = create_rolling_windows(raw_data, WINDOW_SIZE)
    
    # PyTorch LSTM expects a feature dimension. We add a dummy dimension of 1.
    X = X.unsqueeze(-1).float() # Shape: [90, 10, 1]
    y = y.unsqueeze(-1).float() # Shape: [90, 1]
    
    # 3. TEMPORAL SPLIT (DO NOT SHUFFLE!)
    train_size = 70
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    # 4. Predict
    model = TimeSeriesLSTM(input_size=1, hidden_size=32)
    predictions = model(X_test)
    
    print(f"Test Set Input Shape: {X_test.shape} (20 samples, 10 days of history, 1 feature)")
    print(f"Predictions Shape: {predictions.shape} (20 future predictions)")
    print("\nCrucially, we split the data sequentially. The model has never seen the Test future!")

if __name__ == "__main__":
    test_forecaster()
```

### Key Takeaways from Code:
1. **The Rolling Window:** This is the most important concept in Time Series ML. A Neural Network requires a fixed input size. We physically slide a "window" across the timeline to create thousands of independent training examples from a single timeline.
2. **`lstm_out[:, -1, :]`**: Because we only want to predict *one* day into the future, we throw away all the LSTM outputs except for the very last timestep. This last timestep contains the compressed memory of the entire 10-day window!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Multi-Modal Forecasting
Combine NLP with Time Series!
**Your Task:**
1. Conceptually design an architecture that predicts Apple stock.
2. Branch 1: The `TimeSeriesLSTM` processes the past 10 days of numerical stock prices `[Batch, 10, 1]`.
3. Branch 2: A `TextCNN` processes the text of 5 recent news articles about Apple `[Batch, Seq_Len]`.
4. Concatenate the output of the LSTM and the output of the CNN.
5. Pass the combined vector through an `nn.Linear` layer to predict tomorrow's stock price! You have just designed a multi-modal Wall Street quant bot!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are asked to forecast daily inventory demand for 100,000 different products across 500 retail stores. Discuss your approach regarding Model Architecture (Local vs Global models), Feature Engineering, and how you handle 'Cold-Start' products that have no historical data."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Global vs Local Models:** 
   - Explain that training 50 million separate ARIMA models (one for each product/store) is an operational nightmare. 
   - Propose a **Global Neural Model** (like an LSTM or Transformer) that trains on all products simultaneously, allowing it to learn cross-product correlations (e.g., if bread sales go up, peanut butter sales go up).
2. **Feature Engineering:**
   - Mention Time features (Day of week, Month).
   - Mention Lag features (Sales 1 day ago, 7 days ago).
   - Mention Static features (Store Location, Product Category).
3. **The Cold-Start Solution:**
   - Conclude that statistical models fail completely on brand new products. Because you are using a Global Neural Model, the AI can rely entirely on the Static Features. If a new "Strawberry Yogurt" is released, the AI sees its Category Embeddings and mathematically applies the seasonal patterns it learned from "Blueberry Yogurt"!

---
**Task for the end of the day:** Commit your code to Git. 

Take a deep breath. You have completed the first half of the curriculum. Tomorrow, in **Day 56**, we cross a massive threshold. We abandon prediction, and we teach the AI how to **Imagine**. Welcome to the era of **Generative AI and Variational Autoencoders!**
