# Day 43: Vanilla RNNs & Backpropagation Through Time

Welcome to **Phase 3: Sequence Modeling**. 

For the last 42 days, we have studied static, frozen data. An image does not change. A house price is a single row in a spreadsheet. 
But human reality exists in the 4th dimension: **Time**. 

A spoken sentence unfolds across time. The stock market changes every second. If you feed a sequence into a standard <abbr title="Convolutional Neural Network">CNN</abbr>, it fails completely because CNNs expect a fixed input size (e.g., exactly $224 \times 224$). Sentences have varying lengths! To process Time, we must build an <abbr title="Artificial Intelligence">AI</abbr> that possesses a **Memory**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Recurrent Neural Network (<abbr title="Recurrent Neural Network">RNN</abbr>)
A standard Neural Network feeds data straight through: $Input \rightarrow Hidden \rightarrow Output$.
A Recurrent Neural Network (<abbr title="Recurrent Neural Network">RNN</abbr>) has a **Loop**. 
When it processes the 1st word in a sentence, it calculates a Hidden State (a memory vector). When it looks at the 2nd word, it looks at the word *AND* it loops its own memory vector from the previous step back into the equation!
**The Math:** $h_t = \tanh(W_{hh} \cdot h_{t-1} + W_{xh} \cdot x_t)$
- $h_t$: The current memory (What I know at Time=t).
- $h_{t-1}$: The past memory (What I knew 1 second ago).
- $x_t$: The current input (The word I am reading right now).
- $W_{hh}$ and $W_{xh}$: The weights (How important is the past vs. the present?).

### 2. Unrolling Through Time
How do you run Backpropagation (Calculus) on a mathematical loop? You can't. 
To train an <abbr title="Recurrent Neural Network">RNN</abbr>, PyTorch physically **Unrolls** the loop across time. 
If you feed a 10-word sentence into a 1-layer <abbr title="Recurrent Neural Network">RNN</abbr>, PyTorch mathematically unrolls it into a **10-layer deep network**, where each "layer" is a single word in the sequence. 

### 3. Backpropagation Through Time (BPTT)
Once the loop is unrolled, we calculate the error at the end of the sentence, and pass the error backward through all 10 words. This is called **Backpropagation Through Time (BPTT)**. It is just the standard Calculus Chain Rule applied across time.

### 4. The Amnesia Problem (Vanishing Gradients)
RNNs have a fatal, catastrophic flaw. They suffer from instant amnesia.
Look at the math: To carry the memory from Word 1 to Word 10, the network multiplies by the weight matrix $W_{hh}$ exactly 10 times. 
If the weights in $W_{hh}$ are small (e.g., $0.1$), multiplying $0.1 \times 0.1 \times 0.1$ ten times results in $0.0000000001$. 
**The gradient vanishes.** The network completely forgets what Word 1 was by the time it reaches Word 10. It is physically incapable of connecting the start of a sentence to the end of a sentence.

### 5. Exploding Gradients & Gradient Clipping
What if the weights in $W_{hh}$ are large (e.g., $2.0$)? Multiplying $2.0 \times 2.0 \times 2.0$ ten times causes the math to instantly explode to `Infinity` (NaN). 
We solve this using **Gradient Clipping**. Before PyTorch updates the weights, we mathematically chop the gradient off if it exceeds a certain size (e.g., `torch.nn.utils.clip_grad_norm_`).

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Vanilla <abbr title="Recurrent Neural Network">RNN</abbr> entirely from scratch. We will write the `for` loop that passes the Hidden State through time, so you can see exactly how the <abbr title="Artificial Intelligence">AI</abbr> remembers the past.

Create a file named `vanilla_rnn.py`:

```python
import torch
import torch.nn as nn

class VanillaRNN(nn.Module):
    """
    A from-scratch implementation of a Recurrent Neural Network.
    """
    def __init__(self, input_size, hidden_size, output_size):
        super(VanillaRNN, self).__init__()
        
        self.hidden_size = hidden_size
        
        # 1. The Weight Matrix for the INPUT (What I see now)
        self.W_xh = nn.Linear(input_size, hidden_size)
        
        # 2. The Weight Matrix for the HIDDEN STATE (What I remember from the past)
        self.W_hh = nn.Linear(hidden_size, hidden_size)
        
        # 3. The Weight Matrix for the final Prediction
        self.W_hy = nn.Linear(hidden_size, output_size)
        
        # Tanh activation to keep the memory numbers between -1 and +1
        self.tanh = nn.Tanh()

    def forward(self, sequence):
        """
        sequence shape: [Sequence_Length, Batch_Size, Input_Size]
        (e.g., a sentence of 5 words)
        """
        seq_length, batch_size, _ = sequence.shape
        
        # Step 1: Initialize the very first memory to all zeros!
        # Before reading the first word, the AI remembers nothing.
        h_t = torch.zeros(batch_size, self.hidden_size)
        
        # Step 2: Loop through Time! (Read the sentence word by word)
        for t in range(seq_length):
            # Grab the current word
            x_t = sequence[t] 
            
            # THE MAGIC RNN MATH: h_t = tanh( W_hh*h_old + W_xh*x_current )
            # Combine the Past Memory with the Current Word
            memory_from_past = self.W_hh(h_t)
            data_from_present = self.W_xh(x_t)
            
            # Create the New Memory!
            h_t = self.tanh(memory_from_past + data_from_present)
            
        # Step 3: Make a final prediction based on the final memory state
        # (This memory state theoretically contains the context of the whole sentence)
        output = self.W_hy(h_t)
        
        return output

def test_time_loop():
    print("--- RUNNING VANILLA RNN ---")
    
    # Simulate a sentence of 10 words. 
    # Batch=1, Input_Size=5 (e.g., each word is represented by 5 numbers)
    # Shape must be [Seq_Len, Batch, Input_Size]
    sentence = torch.randn(10, 1, 5)
    
    model = VanillaRNN(input_size=5, hidden_size=20, output_size=2)
    
    # Process the sentence!
    prediction = model(sentence)
    
    print(f"Final Prediction Shape: {prediction.shape}")
    print("The RNN looped 10 times, updating its hidden state at every single word, before making this prediction.")

if __name__ == "__main__":
    test_time_loop()
```

### Key Takeaways from Code:
1. **The For Loop:** Notice the `for t in range(seq_length):`. Unlike CNNs which process everything simultaneously, RNNs process data strictly sequentially. This is why RNNs are notoriously slow to train; you cannot mathematically skip ahead to Word 5 until you have finished calculating Word 4.
2. **The Tanh Squeeze:** We use `nn.Tanh()` because it squashes all numbers between -1 and 1. If we used a `ReLU` inside a loop, the numbers would grow larger and larger every iteration until the system exploded instantly.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Gradient Clipping
Because of the loop, <abbr title="Recurrent Neural Network">RNN</abbr> gradients explode easily. You must clip them.
**Your Task:**
1. Write a dummy training loop using the PyTorch built-in `nn.RNN()`.
2. Do the Forward Pass and calculate Loss.
3. Call `loss.backward()`.
4. *Crucial Step:* Before calling `optimizer.step()`, add this line of code:
   `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)`
5. You have just implemented Gradient Clipping. If the calculus gradient exceeds $1.0$, PyTorch mathematically scales it down to exactly $1.0$, preventing the Infinity explosion!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Mathematically prove why Vanilla RNNs are utterly incapable of learning long-term dependencies (e.g., linking a subject at the start of a paragraph to a verb at the end of the paragraph)."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The BPTT Multiplication Chain:** 
   - State that Backpropagation Through Time (BPTT) requires applying the Chain Rule backwards across every timestep. 
   - Explain that calculating the gradient for Time Step 1 requires mathematically multiplying by the hidden weight matrix ($W_{hh}$) exactly $T$ times.
2. **The Eigenvalue Decay:**
   - Explain that if the maximum eigenvalue of the weight matrix $W_{hh}$ is less than 1 (which it usually is to prevent explosion), raising a fraction to the power of 50 (for a 50-word sentence) causes the value to decay exponentially to $0.0$.
3. **The Conclusion:**
   - Conclude that because the error gradient decays to zero before reaching the start of the sequence, the weights responsible for remembering the beginning of the sentence *never receive an update*. The <abbr title="Recurrent Neural Network">RNN</abbr> physically cannot learn the dependency. 
   - *(Note: Tomorrow, we learn how to fix this using LSTMs!)*

---
**Task for the end of the day:** Commit your code to Git. You have successfully conquered Time.

Tomorrow, in **Day 44**, we fix the <abbr title="Recurrent Neural Network">RNN</abbr>'s amnesia problem by inventing mathematical Memory Gates. Welcome to **LSTMs and GRUs!**
