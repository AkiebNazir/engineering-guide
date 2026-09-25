# Day 45: GRU & Bidirectional RNNs

Welcome to Day 45. The <abbr title="Long Short-Term Memory">LSTM</abbr> is a mathematical masterpiece, but it has a massive problem: **<abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr>**.
Because the <abbr title="Long Short-Term Memory">LSTM</abbr> uses 4 separate weight matrices to calculate its gates, it takes up a massive amount of memory and is very slow to train. 

In 2014, researchers discovered a way to streamline the math. They created a network that runs 25% faster than an <abbr title="Long Short-Term Memory">LSTM</abbr>, uses less <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr>, and achieves the exact same accuracy. It is called the **<abbr title="Gated Recurrent Unit">GRU</abbr>**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The <abbr title="Gated Recurrent Unit">GRU</abbr> (Gated Recurrent Unit)
How do you streamline an <abbr title="Long Short-Term Memory">LSTM</abbr>? You aggressively delete parts of it!
1. **Delete the Cell State Highway:** The <abbr title="Gated Recurrent Unit">GRU</abbr> completely removes the $C_t$ Cell State. It goes back to using a single memory stream: the Hidden State ($h_t$).
2. **Combine the Gates:** The <abbr title="Long Short-Term Memory">LSTM</abbr> has a Forget Gate and an Input Gate. The <abbr title="Gated Recurrent Unit">GRU</abbr> combines them into a single **Update Gate ($z_t$)**. 
   - If $z_t = 1.0$, the network *keeps* the old memory and ignores the new word.
   - If $z_t = 0.0$, the network *deletes* the old memory and instantly absorbs the new word. 
   - It is a mathematical seesaw. By forcing the network to choose between the Past and the Present, you only need 1 gate instead of 2!
3. **The Reset Gate ($r_t$):** Used to drop past information *before* calculating the new candidate memory. 

### 2. Bidirectional RNNs
Imagine reading this sentence: *"I sat by the river bank."*
If the <abbr title="Artificial Intelligence">AI</abbr> reads left-to-right, when it hits the word *"bank"*, it thinks of money. It doesn't know it's a river bank until it reads the context, but the context is in the past!
Wait, what about this sentence: *"The bank of the river was muddy."*
When the <abbr title="Artificial Intelligence">AI</abbr> reads *"bank"*, the word *"river"* is in the **future**. Standard RNNs cannot read the future!

**The Solution:** Bidirectional RNNs (BiRNNs).
You spin up *two* separate LSTMs. 
- <abbr title="Long Short-Term Memory">LSTM</abbr> #1 reads the sentence left-to-right.
- <abbr title="Long Short-Term Memory">LSTM</abbr> #2 reads the sentence right-to-left (backwards).
When you ask the network what the word "bank" means, it literally concatenates the memory of <abbr title="Long Short-Term Memory">LSTM</abbr> #1 (the Past) with the memory of <abbr title="Long Short-Term Memory">LSTM</abbr> #2 (the Future). The <abbr title="Artificial Intelligence">AI</abbr> suddenly has perfect 360-degree context!

### 3. Deep RNNs
Just like CNNs, you can stack RNNs on top of each other. The output of <abbr title="Recurrent Neural Network">RNN</abbr> Layer 1 becomes the input sequence for <abbr title="Recurrent Neural Network">RNN</abbr> Layer 2. However, unlike CNNs which can be 150 layers deep, RNNs rarely go beyond 3 to 5 layers. Because they already loop through time, a 3-layer <abbr title="Recurrent Neural Network">RNN</abbr> reading a 50-word sentence is mathematically equivalent to a 150-layer deep network! Stacking them too deep causes severe instability.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Bidirectional <abbr title="Gated Recurrent Unit">GRU</abbr> from scratch in PyTorch to see exactly how the "Forward" and "Backward" memory streams are concatenated.

Create a file named `gru_bidirectional.py`:

```python
import torch
import torch.nn as nn

class BiGRU_Tagger(nn.Module):
    """
    A Bidirectional GRU used for Part-of-Speech Tagging
    (e.g., labeling words as Nouns, Verbs, Adjectives).
    """
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_tags):
        super(BiGRU_Tagger, self).__init__()
        
        # 1. Turn word IDs (e.g., Word #452) into mathematical vectors
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        
        # 2. THE Bi-GRU
        # Setting bidirectional=True tells PyTorch to automatically spin up a second GRU
        # and feed the sentence into it backwards!
        self.gru = nn.GRU(input_size=embedding_dim, 
                          hidden_size=hidden_size, 
                          batch_first=True, 
                          bidirectional=True)
                          
        # 3. The Output Layer
        # CRITICAL MATH: Because the GRU is bidirectional, it spits out 
        # TWO hidden states (Forward + Backward). We must multiply hidden_size * 2!
        self.fc = nn.Linear(hidden_size * 2, num_tags)

    def forward(self, sentence_tensor):
        # 1. Embed the words
        # Shape: [Batch, Seq_Len, Embed_Dim]
        embeds = self.embedding(sentence_tensor)
        
        # 2. Pass through the Bi-GRU
        # gru_out contains the concatenated [Forward, Backward] states for EVERY word
        gru_out, final_hidden = self.gru(embeds)
        
        # 3. Predict the Part-of-Speech tag for every single word
        # Shape: [Batch, Seq_Len, Num_Tags]
        tag_predictions = self.fc(gru_out)
        
        return tag_predictions

def test_bigru():
    print("--- RUNNING BIDIRECTIONAL GRU ---")
    
    # Simulate a Batch of 1 sentence, containing 7 words.
    # The numbers are the IDs of the words in the dictionary.
    sentence = torch.tensor([[12, 45, 8, 99, 2, 4, 15]]) 
    print(f"Input Sentence Shape: {sentence.shape}")
    
    # Initialize the model
    # Vocab Size: 1000 words. Hidden Size: 20. Output Tags: 5 (Noun, Verb, etc).
    model = BiGRU_Tagger(vocab_size=1000, embedding_dim=10, hidden_size=20, num_tags=5)
    
    predictions = model(sentence)
    
    print(f"Predictions Shape: {predictions.shape}")
    print("Notice the shape: [1, 7, 5]. For all 7 words, the AI predicted 5 probability scores.")
    print("Because it is Bidirectional, the AI used future words to help label past words!")

if __name__ == "__main__":
    test_bigru()
```

### Key Takeaways from Code:
1. **`bidirectional=True`:** This single argument is magic. Under the hood, PyTorch reverses the sequence array, runs a second independent <abbr title="Gated Recurrent Unit">GRU</abbr>, reverses the output back, and glues the two matrices together.
2. **`hidden_size * 2`:** If you forget to double the input size of the `nn.Linear` layer, PyTorch will crash. If your hidden size is 20, the Forward <abbr title="Gated Recurrent Unit">GRU</abbr> outputs 20 numbers, and the Backward <abbr title="Gated Recurrent Unit">GRU</abbr> outputs 20 numbers. The final concatenated memory for the word is 40 numbers!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: <abbr title="Gated Recurrent Unit">GRU</abbr> vs <abbr title="Long Short-Term Memory">LSTM</abbr> Math
The <abbr title="Gated Recurrent Unit">GRU</abbr> uses a single Update Gate ($z_t$) to replace the Forget and Input gates. 
The Math: $h_t = (1 - z_t) * h_{t-1} + (z_t) * \tilde{h}_t$
**Your Task:**
1. Look at the math equation above.
2. If $z_t$ evaluates to exactly $1.0$, what happens to the Past Memory ($h_{t-1}$)? (Answer: It is multiplied by $(1-1) = 0$, completely deleting the past).
3. If $z_t$ evaluates to exactly $0.0$, what happens to the New Memory ($\tilde{h}_t$)? (Answer: It is multiplied by $0$, completely ignoring the new word).
4. Realize the genius of this constraint: The <abbr title="Gated Recurrent Unit">GRU</abbr> is physically forced to balance the budget. If it wants to remember 80% of the past, it is only allowed to absorb 20% of the present!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Bidirectional RNNs provide massive boosts to accuracy by allowing the network to see the 'Future' context of a word. However, you are tasked with building a Real-Time Speech Translation system for a live video call. Why is it mathematically impossible to use a Bidirectional <abbr title="Recurrent Neural Network">RNN</abbr> for this product, and what architectural alternatives exist?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Causality Flaw of BiRNNs:** 
   - State that a Bidirectional <abbr title="Recurrent Neural Network">RNN</abbr> requires the entire sequence to be present in <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> before it can process the very first word (because the Backward <abbr title="Recurrent Neural Network">RNN</abbr> must start at the end of the sentence and read backwards).
   - In a Live Video Call, the user is currently speaking. The end of the sentence literally does not exist yet. The <abbr title="Artificial Intelligence">AI</abbr> would have to wait in silence for the user to finish their entire paragraph before translating the first word, causing unacceptable latency.
2. **The Alternative (Causal/Unidirectional):**
   - Explain that for real-time streaming, you must use strictly **Unidirectional** (Causal) LSTMs or GRUs, which only process data from Left-to-Right.
   - Mention that you can use a sliding "Look-ahead" window. If you delay the translation by just 300 milliseconds, you can capture 2 or 3 future words, giving the Unidirectional model enough context to translate accurately without requiring the entire sentence!

---
**Task for the end of the day:** Commit your code to Git. You have streamlined the memory architecture.

Tomorrow, in **Day 46**, we tackle the hardest problem in Sequence Modeling. How do you translate English to French when the sentences have different lengths? Welcome to **Seq2Seq and The Bottleneck Problem!**
