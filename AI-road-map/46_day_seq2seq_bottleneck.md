# Day 46: Seq2Seq Models & The Bottleneck Problem

Welcome to Day 46. You have built LSTMs and GRUs that can read a sentence and output a single classification (e.g., "Positive Sentiment").
But what if you want to build Google Translate? What if you want to input a 10-word English sentence, and output a 14-word French sentence?

Standard RNNs require the Input and Output sizes to be identical. You cannot translate 10 words into 14 words. 
To solve this, we must build two completely separate neural networks and bolt them together. Welcome to the **Seq2Seq (Encoder-Decoder) Architecture**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Encoder-Decoder Architecture
Seq2Seq splits the translation task into two phases:
1. **The Encoder (The Reader):** An <abbr title="Long Short-Term Memory">LSTM</abbr> that reads the English sentence word by word. It does not output any predictions. Its only job is to update its Hidden State ($h_t$). When it finishes reading the final word, its final Hidden State contains the mathematical "meaning" of the entire English sentence. This final state is called the **Context Vector**.
2. **The Decoder (The Writer):** A completely separate <abbr title="Long Short-Term Memory">LSTM</abbr>. We inject the Context Vector directly into its brain. The Decoder then starts predicting the French translation, one word at a time, until it outputs a special `<END>` token.

### 2. Teacher Forcing (Exposure Bias)
Training the Decoder is incredibly difficult. 
If the correct French sentence is *"Je suis un chat"*, but the Decoder accidentally hallucinates and outputs *"Tu"* for the first word, the <abbr title="Long Short-Term Memory">LSTM</abbr> will feed *"Tu"* back into itself for step 2. The entire rest of the sentence is now mathematically doomed!
**The Fix:** **Teacher Forcing**. During training, even if the <abbr title="Artificial Intelligence">AI</abbr> guesses *"Tu"*, we physically intercept the loop and force the correct word (*"Je"*) into the input of Step 2. This keeps the network mathematically stable during training.

### 3. Beam Search
During inference (production), Teacher Forcing is turned off. 
If the <abbr title="Artificial Intelligence">AI</abbr> just greedily picks the #1 most confident word at every step, it often writes sentences that are grammatically broken.
**Beam Search** fixes this. Instead of picking the #1 word, it picks the Top 3 words (Beam Width = 3). It then branches out and simulates the entire rest of the sentence for all 3 paths! Finally, it multiplies the probabilities of the entire sentence together and picks the path that makes the most global sense.

### 4. The Bottleneck Problem (The Fatal Flaw)
Seq2Seq changed the world, but it has a catastrophic physical flaw.
Look at the Encoder. If you feed it a 500-word paragraph, it must compress the meaning of all 500 words into a *single* Context Vector (e.g., an array of 512 numbers).
**This is an Information Bottleneck.** It is mathematically impossible to compress 500 words of complex human thought into 512 numbers without destroying massive amounts of information. The Decoder receives a corrupted, heavily compressed vector, and the translation fails. *(Tomorrow, in Day 47, we learn how Attention was invented to fix this).*

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the Seq2Seq architecture in PyTorch. You will see exactly how the `hidden_state` is physically passed from the Encoder to the Decoder!

Create a file named `seq2seq_translation.py`:

```python
import torch
import torch.nn as nn
import random

class Encoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_size):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.gru = nn.GRU(embed_dim, hidden_size, batch_first=True)
        
    def forward(self, source_text):
        embedded = self.embedding(source_text)
        
        # We don't care about the 'outputs'. We ONLY care about the final 'hidden' state!
        outputs, hidden = self.gru(embedded)
        
        # This 'hidden' is the Context Vector! It contains the compressed English sentence.
        return hidden

class Decoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_size):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.gru = nn.GRU(embed_dim, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, vocab_size)
        
    def forward(self, input_word, hidden):
        # input_word shape: [Batch, 1] (We pass one word at a time!)
        embedded = self.embedding(input_word)
        
        # We feed the embedded word AND the hidden state from the previous step!
        output, hidden = self.gru(embedded, hidden)
        
        # Predict the translation for this specific word
        prediction = self.fc(output)
        
        return prediction, hidden

class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        
    def forward(self, source, target, teacher_forcing_ratio=0.5):
        batch_size = source.shape[0]
        target_len = target.shape[1]
        target_vocab_size = self.decoder.fc.out_features
        
        # Tensor to store the final French predictions
        outputs = torch.zeros(batch_size, target_len, target_vocab_size)
        
        # 1. RUN THE ENCODER!
        # Compress the entire English sentence into the Context Vector
        hidden = self.encoder(source)
        
        # 2. RUN THE DECODER!
        # The first input to the decoder is always the <START> token (e.g., index 0)
        decoder_input = target[:, 0].unsqueeze(1)
        
        # Loop through the length of the French sentence
        for t in range(1, target_len):
            
            # Pass the input word and the Hidden State into the Decoder!
            # Notice how 'hidden' is continuously updated and passed to the next step
            prediction, hidden = self.decoder(decoder_input, hidden)
            
            # Save the prediction
            outputs[:, t, :] = prediction.squeeze(1)
            
            # Teacher Forcing: Do we use the True word, or the AI's predicted word for the next step?
            best_guess = prediction.argmax(dim=2)
            
            if random.random() < teacher_forcing_ratio:
                # Force the true answer
                decoder_input = target[:, t].unsqueeze(1)
            else:
                # Let the AI use its own guess
                decoder_input = best_guess
                
        return outputs

def test_seq2seq():
    print("--- RUNNING SEQ2SEQ TRANSLATOR ---")
    
    # 1. Setup
    ENC_VOCAB = 1000 # English Dictionary Size
    DEC_VOCAB = 1500 # French Dictionary Size
    HIDDEN_SIZE = 256
    
    encoder = Encoder(ENC_VOCAB, embed_dim=128, hidden_size=HIDDEN_SIZE)
    decoder = Decoder(DEC_VOCAB, embed_dim=128, hidden_size=HIDDEN_SIZE)
    model = Seq2Seq(encoder, decoder)
    
    # 2. Simulate Data
    # English Sentence: 10 words long
    english = torch.randint(0, ENC_VOCAB, (1, 10))
    # French Target: 14 words long
    french = torch.randint(0, DEC_VOCAB, (1, 14))
    
    # 3. Translate!
    outputs = model(english, french)
    
    print(f"English Input Shape:  {english.shape}")
    print(f"French Target Shape:  {french.shape}")
    print(f"Decoder Output Shape: {outputs.shape}")
    print("Success! The AI bypassed the length restrictions by using an intermediate Context Vector.")

if __name__ == "__main__":
    test_seq2seq()
```

### Key Takeaways from Code:
1. **The Hand-Off:** Look inside `Seq2Seq.forward()`. `hidden = self.encoder(source)`. That single variable `hidden` is the bridge. It is instantly handed off to `self.decoder(decoder_input, hidden)`. The entire intelligence of the system relies on that single vector not being corrupted.
2. **The Decoding Loop:** Notice that the Decoder requires a `for` loop. It generates the French sentence exactly one word at a time. It cannot parallelize this. If a sentence is 50 words long, it must wait for loop 49 to finish before calculating loop 50.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Beam Search Mathematics
Let's understand why greedy decoding fails.
**Your Task:**
1. The <abbr title="Artificial Intelligence">AI</abbr> is translating: *"I am full"*. 
2. Step 1 (Greedy): The <abbr title="Artificial Intelligence">AI</abbr> predicts *"Je"* (90%), *"Tu"* (5%). It picks *"Je"*.
3. Step 2 (Greedy): Following *"Je"*, the <abbr title="Artificial Intelligence">AI</abbr> predicts *"suis"* (80%), *"mangé"* (10%). It picks *"suis"*. (Sentence: *"Je suis"*)
4. Step 3 (Greedy): Following *"Je suis"*, the <abbr title="Artificial Intelligence">AI</abbr> predicts *"plein"* (60%) [Meaning: physically full of food]. Total path probability: $0.90 \times 0.80 \times 0.60 = \mathbf{0.432}$.
5. Now, run Beam Search. Instead of picking *"Je"*, Beam Search explores *"J'ai"* (I have) which had a lower Step 1 probability of 70%.
6. Following *"J'ai"*, it predicts *"mangé"* (95%).
7. Following *"mangé"*, it predicts *"assez"* (I have eaten enough) (85%). 
8. Calculate the math: $0.70 \times 0.95 \times 0.85 = \mathbf{0.565}$.
9. *The result:* Even though *"J'ai"* was the second-best word at Step 1, it lead to a globally better, more fluent sentence overall! Greedy decoding completely missed it.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You deploy a Seq2Seq translation model to production. The metrics show it translates 5-word sentences with 98% accuracy. However, when users input 50-word paragraphs, the accuracy drops to 12%. Diagnose the fundamental architectural root cause of this degradation, and propose the specific mathematical solution."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Root Cause (The Information Bottleneck):** 
   - State clearly that standard Seq2Seq models force the Encoder to compress the entirety of the input sequence into a single, fixed-size Context Vector (the final hidden state).
   - Explain that a 50-word paragraph contains too much complex syntactic and semantic information to mathematically fit into an array of 512 floats. The front half of the paragraph suffers from the Vanishing Gradient problem and is overwritten by the end of the paragraph. The Decoder is essentially starved of information.
2. **The Solution (Attention):**
   - Propose implementing an **Attention Mechanism** (Bahdanau or Luong).
   - Explain that Attention allows the Decoder to "look backward" across the entire English sentence at *every single decoding step*. Instead of relying on 1 compressed vector, the Decoder dynamically calculates a weighted average of all 50 English words, deciding which specific English word to focus on right now to predict the current French word.

---
**Task for the end of the day:** Commit your code to Git. You have successfully built a real-world translator.

Tomorrow, in **Day 47**, we solve the Bottleneck problem. We will implement the breakthrough technology that changed Artificial Intelligence forever: **The Attention Mechanism!**
