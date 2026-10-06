# Day 50: Sequence Labeling (CRF & Viterbi Decoding)

Welcome to Day 50. Today we tackle one of the most commercially valuable tasks in NLP: **Named Entity Recognition (NER)**.

If you feed a legal contract into an AI, you want the AI to read the document and highlight every single Person, Company, Date, and Dollar Amount. 
To do this, the AI must label *every single word* in the sequence. But standard RNNs fail at this because they make incredibly stupid grammatical mistakes. Today, we fix the RNN using statistical math.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The BIO Tagging Scheme
How do you label the phrase: *"New York City"*? If you label all three words as `LOCATION`, how does the AI know it's not 3 separate cities?
We use the **BIO Scheme**:
- **B** (Beginning): `B-LOC` (The start of New York City)
- **I** (Inside): `I-LOC` (The middle/end of New York City)
- **O** (Outside): `O` (Normal words like "The", "and")
So *"I flew to New York City"* is labeled: `[O, O, O, B-LOC, I-LOC, I-LOC]`.

### 2. The RNN Flaw
If you use a standard BiLSTM to predict these tags, it looks at the words, but it *does not look at the tags it just predicted*. 
Because of this, the BiLSTM might mathematically output: `[O, I-LOC, B-PER, I-LOC]`. 
This is grammatically impossible! 
1. You cannot have an `I-LOC` without a `B-LOC` coming right before it. 
2. You cannot transition from `B-PER` (Person) directly into `I-LOC` (Location)!

### 3. Conditional Random Fields (CRF)
A **CRF** is a mathematical layer we bolt onto the very end of our Neural Network. 
The CRF maintains a **Transition Matrix**. During training, it looks at the data and learns the probabilities of moving from one tag to another.
It learns that moving from `B-PER` to `I-LOC` has a $0.0\%$ chance of ever happening. 
When the BiLSTM makes its prediction, the CRF intercepts the prediction, checks its Transition Matrix, and mathematically vetoes any sequence of tags that violates the rules of grammar!

### 4. Viterbi Decoding (Dynamic Programming)
If a sentence has 10 words, and there are 5 possible tags for each word, the AI must search through $5^{10} = 9,765,625$ possible tag combinations to find the one sequence with the highest total probability score. Calculating 9 million paths takes too long.
**Viterbi Decoding** is a dynamic programming algorithm. As it walks left-to-right across the sentence, it only remembers the *best possible path* to get to each tag, and instantly deletes all inferior paths. This drops the compute time from Exponential $O(T^N)$ down to Linear $O(N \cdot T^2)$!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the Viterbi Decoding algorithm entirely from scratch in Python. You will see how it uses a `for` loop to step through time, remembering only the maximum probabilities!

Create a file named `crf_viterbi.py`:

```python
import torch

def viterbi_decode(emissions, transitions, start_transitions, end_transitions):
    """
    Finds the absolutely most probable sequence of tags.
    
    emissions: [Seq_Len, Num_Tags] (The raw guesses from the BiLSTM)
    transitions: [Num_Tags, Num_Tags] (The CRF matrix: Score of moving from Tag_i to Tag_j)
    start_transitions: [Num_Tags] (Score of starting a sentence with this tag)
    end_transitions: [Num_Tags] (Score of ending a sentence with this tag)
    """
    seq_len, num_tags = emissions.shape
    
    # 1. Initialize the Viterbi variables
    # This tensor holds the maximum score to reach each tag at the CURRENT timestep
    # We add the Start probabilities to the BiLSTM's guesses for Word 1!
    viterbi_scores = start_transitions + emissions[0]
    
    # We must remember our path so we can walk backwards at the end!
    backpointers = []
    
    # 2. Walk through Time (Word 2 to the end)
    for t in range(1, seq_len):
        current_bptrs = []
        current_scores = []
        
        # We are trying to find the best way to get to NEXT_TAG
        for next_tag in range(num_tags):
            # The math: Score of getting to Prev_Tag + Transition Score + BiLSTM guess
            # Notice we broadcast this across ALL Prev_Tags simultaneously!
            transition_scores = viterbi_scores + transitions[:, next_tag]
            
            # Find the absolute best previous tag that leads to this next_tag
            best_prev_tag = torch.argmax(transition_scores)
            best_score = transition_scores[best_prev_tag]
            
            current_bptrs.append(best_prev_tag.item())
            # Add the BiLSTM's guess for this exact word
            current_scores.append(best_score + emissions[t, next_tag])
            
        # Save the path
        backpointers.append(current_bptrs)
        
        # Update the running Viterbi scores for the next timestep
        viterbi_scores = torch.tensor(current_scores)
        
    # 3. Add the End-of-Sentence transition scores
    viterbi_scores += end_transitions
    
    # Find the absolute best tag to END the sentence on
    best_last_tag = torch.argmax(viterbi_scores).item()
    best_path_score = viterbi_scores[best_last_tag].item()
    
    # 4. Walk Backwards through the Backpointers to rebuild the path!
    best_path = [best_last_tag]
    for bptrs_t in reversed(backpointers):
        best_last_tag = bptrs_t[best_last_tag]
        best_path.append(best_last_tag)
        
    # Reverse the path so it goes left-to-right
    best_path.reverse()
    
    return best_path, best_path_score

def test_viterbi():
    print("--- RUNNING VITERBI DECODING ---")
    
    NUM_TAGS = 3 # 0: O, 1: B-PER, 2: I-PER
    SEQ_LEN = 4  # A 4-word sentence
    
    # The raw guesses from the BiLSTM for the 4 words
    emissions = torch.randn(SEQ_LEN, NUM_TAGS)
    
    # The CRF Transition Matrix (From Row -> To Col)
    transitions = torch.randn(NUM_TAGS, NUM_TAGS)
    
    # Let's FORCE a rule: Moving from O (0) directly to I-PER (2) is IMPOSSIBLE!
    # We set the transition score to -10,000!
    transitions[0, 2] = -10000.0
    
    start_trans = torch.randn(NUM_TAGS)
    end_trans = torch.randn(NUM_TAGS)
    
    best_path, score = viterbi_decode(emissions, transitions, start_trans, end_trans)
    
    print(f"CRF Transition Matrix (O -> I-PER) set to -10000.0")
    print(f"Viterbi found the Best Path: {best_path}")
    print("Notice that the sequence [0, 2] will NEVER appear in the path, because the CRF mathematically forbade it!")

if __name__ == "__main__":
    test_viterbi()
```

### Key Takeaways from Code:
1. **The For Loop:** `for next_tag in range(num_tags):` and `torch.argmax(transition_scores)`. This is the core of dynamic programming. It calculates the scores for all paths leading to `next_tag`, and immediately throws away all of them except the `argmax`. It doesn't waste RAM remembering bad paths!
2. **The Backpointers:** You can't know the best path until you reach the end of the sentence. The `backpointers` array acts as a trail of breadcrumbs. Once we find the best final tag, we follow the breadcrumbs backwards to reconstruct the perfect sequence.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The BiLSTM-CRF Pipeline
A CRF is never used alone. It is placed on top of an RNN.
**Your Task:**
1. Conceptually map out the architecture of a `BiLSTM_CRF` PyTorch module.
2. Layer 1: `nn.Embedding` (Turns words into 300D vectors).
3. Layer 2: `nn.LSTM(bidirectional=True)` (Reads the sentence forward and backward).
4. Layer 3: `nn.Linear` (Projects the LSTM output down to `NUM_TAGS`). This creates the `emissions` tensor!
5. Layer 4: The `viterbi_decode` function you wrote above.
6. Realize that during inference, you run the BiLSTM to get the `emissions`, and then pass them into the Viterbi decoder to get the final cleaned tags!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your Named Entity Recognition system achieves 95% F1 score on formal Bloomberg news articles. However, when deployed to Twitter/X to analyze financial tweets, the F1 score drops to 40%. Diagnose the root cause of this failure, and propose three specific technical solutions that do NOT require manually labeling a new Twitter dataset."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Diagnosis (Domain Shift & OOV):** 
   - Explain that formal text uses standard grammar, capitalization, and punctuation (which the BiLSTM heavily relies on). 
   - Twitter text uses slang, emojis, missing punctuation, and deliberate misspellings. This causes massive Out-Of-Vocabulary (OOV) errors and breaks the grammatical context the BiLSTM expects.
2. **Solution 1: Subword Tokenization (BPE/FastText):**
   - Replace standard Word2Vec with **FastText** or **BPE**. FastText embeds sub-character n-grams, allowing the model to mathematically guess the meaning of misspelled words (e.g., "awesssome") by looking at the sub-characters.
3. **Solution 2: Rule-Based / Dictionary Matching (Weak Supervision):**
   - Use gazetteers (massive lists of known companies/people) combined with Regex to automatically tag obvious entities in the tweets, generating a "weakly labeled" dataset to fine-tune the model.
4. **Solution 3: Zero-Shot / Few-Shot LLMs:**
   - Use a pre-trained Large Language Model (like LLaMA-3 or GPT) and pass it a zero-shot prompt: *"Extract the organizations from this tweet: <tweet>"*. Modern LLMs are highly robust to informal text out-of-the-box.

---
**Task for the end of the day:** Commit your code to Git. You have successfully conquered Sequence Labeling.

Tomorrow, in **Day 51**, we return to Document Classification. We will learn how to use CNNs to read text (**TextCNN**), and how to read massive documents using **Hierarchical Attention Networks!**
