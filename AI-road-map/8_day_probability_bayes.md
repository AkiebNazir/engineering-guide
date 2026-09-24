# Day 8: Probability Axioms & Bayes' Theorem

Welcome to Phase 2! You have officially survived the deterministic world of Linear Algebra and Calculus. 

In Phase 1, if you multiplied $2 \times 3$, the answer was always $6$. But the real world is noisy, unpredictable, and full of missing information. How do we teach an AI to make decisions when it doesn't have all the facts? We use **Probability**. 

Today, we learn how AI models uncertainty, how they update their beliefs when they see new evidence, and the mathematical theorem that underpins everything from spam filters to self-driving cars.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. The Rules of the Universe (Kolmogorov Axioms)
Before we can calculate probabilities, we have to agree on the fundamental laws of the universe. In the 1930s, Andrey Kolmogorov mathematically proved that all probability rests on just three unbreakable axioms *(self-evident truths that require no proof)*.

1. **Non-negativity:** The probability of any event is always $\ge 0$. You cannot have a $-15\%$ chance of rain.
2. **Unit Measure:** The probability of *all* possible events in the universe combined must exactly equal $1.0$ (or $100\%$). 
3. **Additivity:** If two events are **Mutually Exclusive** *(meaning they absolutely cannot happen at the same time, like flipping a coin and getting both Heads and Tails)*, the probability of either happening is just their sum: $P(A \text{ or } B) = P(A) + P(B)$.

> **Mathematical Example (Concrete Numbers):**
> Let's roll a standard 6-sided die.
> Rule 1: $P(\text{rolling a 4}) = \frac{1}{6}$. This is $\ge 0$.
> Rule 2: $P(1) + P(2) + P(3) + P(4) + P(5) + P(6) = \frac{6}{6} = 1.0$.
> Rule 3: $P(\text{rolling a 1 OR a 2}) = P(1) + P(2) = \frac{1}{6} + \frac{1}{6} = \frac{2}{6}$.
> 
> **AI Context (The Softmax Function):** 
> When an LLM like ChatGPT guesses the next word, it outputs a raw array of numbers (logits). Some are negative, some are huge. The AI applies a "Softmax" function to these numbers. Softmax mathematically forces the outputs to obey the Kolmogorov Axioms: it squishes all negative numbers to be $\ge 0$, and forces the entire array to sum perfectly to $1.0$. Without Softmax, the AI's output is mathematically meaningless.

### 2. Joint, Marginal, and Conditional Probability
To understand how variables interact, we use three distinct viewpoints:

- **Joint Probability $P(A, B)$:** The probability of $A$ and $B$ happening at the exact same time.
- **Marginal Probability $P(A)$:** The probability of $A$ happening, completely ignoring what $B$ is doing.
- **Conditional Probability $P(A|B)$:** The probability of $A$ happening, *assuming* we already know $B$ happened.

> **Mathematical Example (Concrete Numbers):**
> Let's draw a single card from a standard 52-card deck.
> **Joint $P(\text{Red}, \text{King})$:** There are only 2 Red Kings in the deck. $P = \frac{2}{52} = 3.8\%$.
> **Marginal $P(\text{Red})$:** Half the deck is red, regardless of the face value. $P = \frac{26}{52} = 50\%$.
> **Conditional $P(\text{King} | \text{Red})$:** Imagine I draw a card, peek at it, and tell you "It is Red!" Now, your universe has shrunk from 52 cards to only 26 cards. Out of those 26 red cards, 2 are Kings. $P = \frac{2}{26} = 7.6\%$. 
> 
> **AI Context (Language Modeling):** 
> Large Language Models (LLMs) are purely massive Conditional Probability engines. When generating text, they calculate $P(\text{Word}_n | \text{Word}_{n-1}, \text{Word}_{n-2}, \dots)$. They are calculating the probability of the *next* word, strictly conditional on the context of the words that came before it.

### 3. Bayes' Theorem: How to Update Your Beliefs
Bayes' Theorem is the mathematical formula for learning from experience. It tells you exactly how to update your beliefs when you are presented with new evidence.

**Algebraic Definition:**
$$ P(A|B) = \frac{P(B|A)P(A)}{P(B)} $$

Where:
- $P(A)$ is the **Prior** *(your initial belief before seeing any new data)*.
- $P(B|A)$ is the **Likelihood** *(how mathematically likely the new data is, assuming your belief is actually true)*.
- $P(B)$ is the **Evidence / Marginal Likelihood** *(the total probability of seeing this data under all possible circumstances)*.
- $P(A|B)$ is the **Posterior** *(your newly updated, smarter belief after combining your Prior with the Likelihood)*.

> **Mathematical Example (Concrete Numbers):**
> You get tested for a rare disease. 
> The **Prior** $P(\text{Disease})$: Only $1\%$ of the population has it ($0.01$).
> The **Likelihood** $P(\text{Positive Test} | \text{Disease})$: The test is very accurate. If you are sick, it detects it $90\%$ of the time ($0.90$).
> The **Evidence** $P(\text{Positive Test})$: The overall rate of positive tests in the hospital is $5\%$ ($0.05$).
> You test positive! Are you doomed? Let's use Bayes' Theorem:
> $P(\text{Disease} | \text{Positive Test}) = \frac{0.90 \times 0.01}{0.05} = \frac{0.009}{0.05} = 0.18$
> **Result:** Even though the test is 90% accurate, because the disease is so rare, you only have an **18% chance** of actually being sick! 
> 
> **AI Context (Machine Learning Core):** 
> This is how AI "learns". Initially, a neural network's weights are random (The Prior). It looks at a batch of training data and sees how likely that data is given its current weights (The Likelihood). It then uses calculus to update its weights to become smarter (The Posterior). That Posterior then becomes the *new* Prior for the next batch of data!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's build a classic AI system entirely from scratch using only Probability: A **Naive Bayes Spam Classifier**. 

It is called "Naive" because it makes the massive assumption that every word in an email is completely independent of every other word *(which is linguistically false, but mathematically highly effective)*.

Create a file named `naive_bayes.py`:

```python
import numpy as np
from collections import defaultdict

class NaiveBayesSpamFilter:
    def __init__(self):
        # We use dictionaries to count how often words appear in Spam vs Ham (Not Spam)
        self.spam_word_counts = defaultdict(int)
        self.ham_word_counts = defaultdict(int)
        
        # P(Spam) and P(Ham) - Our Priors
        self.p_spam = 0.0
        self.p_ham = 0.0
        
        # Total word counts
        self.total_spam_words = 0
        self.total_ham_words = 0
        
        # The size of our entire vocabulary across all emails
        self.vocab_size = 0

    def train(self, emails: list[str], labels: list[int]):
        """
        Calculates the Priors and Likelihoods from the training data.
        labels: 1 for Spam, 0 for Ham.
        """
        print("--- TRAINING NAIVE BAYES ---")
        num_emails = len(emails)
        num_spam = sum(labels)
        
        # 1. Calculate Priors (P(A))
        self.p_spam = num_spam / num_emails
        self.p_ham = (num_emails - num_spam) / num_emails
        
        vocab = set()
        
        # 2. Count Words to establish Likelihoods (P(B|A))
        for email, label in zip(emails, labels):
            words = email.lower().split()
            for word in words:
                vocab.add(word)
                if label == 1:
                    self.spam_word_counts[word] += 1
                    self.total_spam_words += 1
                else:
                    self.ham_word_counts[word] += 1
                    self.total_ham_words += 1
                    
        self.vocab_size = len(vocab)
        print(f"Training complete. Vocab Size: {self.vocab_size}. P(Spam): {self.p_spam:.2f}")

    def predict(self, email: str) -> str:
        """
        Uses Bayes Theorem to calculate the Posterior probability of Spam vs Ham.
        """
        words = email.lower().split()
        
        # We start with the Prior probability
        # Note: We use Logarithms to prevent 'Underflow'. Multiplying tiny probabilities 
        # (e.g., 0.01 * 0.01 * 0.01) quickly turns into 0.00000 on a computer.
        # log(A * B) = log(A) + log(B)
        log_prob_spam = np.log(self.p_spam)
        log_prob_ham = np.log(self.p_ham)
        
        for word in words:
            # LAPLACE SMOOTHING
            # What if we see a word in a new email we NEVER saw in training?
            # The probability would be 0/Total. Multiplying by 0 wipes out all other math.
            # We add 1 to the numerator, and add the Vocab Size to the denominator to fix this!
            
            # Likelihood: P(Word | Spam)
            word_spam_prob = (self.spam_word_counts[word] + 1) / (self.total_spam_words + self.vocab_size)
            log_prob_spam += np.log(word_spam_prob)
            
            # Likelihood: P(Word | Ham)
            word_ham_prob = (self.ham_word_counts[word] + 1) / (self.total_ham_words + self.vocab_size)
            log_prob_ham += np.log(word_ham_prob)
            
        # The higher log probability wins!
        if log_prob_spam > log_prob_ham:
            return "SPAM 🛑"
        else:
            return "HAM 🟢"

if __name__ == "__main__":
    # Synthetic Dataset
    training_emails = [
        "win a free rolex watch now",        # Spam
        "click here for cheap medication",   # Spam
        "urgent update your account details",# Spam
        "hey are we still on for lunch",     # Ham
        "please review the attached report", # Ham
        "meeting pushed to three pm today"   # Ham
    ]
    labels = [1, 1, 1, 0, 0, 0]
    
    classifier = NaiveBayesSpamFilter()
    classifier.train(training_emails, labels)
    
    # Test on unseen emails
    test_1 = "urgent click here to win"
    test_2 = "please review the lunch menu"
    test_3 = "rolex" # Testing a single highly-spammy word
    
    print(f"\nTesting: '{test_1}' -> {classifier.predict(test_1)}")
    print(f"Testing: '{test_2}' -> {classifier.predict(test_2)}")
    print(f"Testing: '{test_3}' -> {classifier.predict(test_3)}")
```

### Key Takeaways from Code:
1. **Log-Probabilities:** Because probabilities are decimals between 0 and 1, multiplying thousands of them together (for a long email) will cause a computer's 32-bit float limit to round the answer to absolute zero (Underflow). By taking the `np.log()` of the probabilities, we can safely *add* them together instead!
2. **Laplace Smoothing:** Notice the `+ 1` in the math. This is a critical statistical trick. If your AI encounters a completely new word it has never seen before, its count is 0. If you don't add 1, the probability $P(\text{Word}) = 0$, and multiplying *anything* by 0 destroys the entire equation. Laplace smoothing ensures no probability is ever truly zero.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Medical Diagnostic AI
**Your Task:** Create a file named `diagnostic_bayes.py`.

You are building an AI tool for doctors. 
1. The disease **Z-Flu** affects 3% of the population (The Prior).
2. The AI uses a symptom checker. If a patient has Z-Flu, they have a 85% chance of reporting a "Fever" (The Likelihood).
3. If a patient does *not* have Z-Flu (they are just healthy/have a cold), they still have a 20% chance of reporting a "Fever" (The False Positive Likelihood).
4. Write a script that asks the user if they have a fever (Yes/No).
5. If they say Yes, use Bayes' Theorem to calculate the exact percentage chance they have Z-Flu, and print it to the screen. 

*Hint: You will need to calculate the Evidence $P(\text{Fever})$ by adding the probability of having a fever while sick AND the probability of having a fever while healthy!*

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"A production fraud detection system for our payment gateway processes 10 million transactions a day. The base rate of fraud is incredibly low: 0.1%. Your new ML model has 99% Recall (it catches 99% of actual fraud) and 95% Precision (when it flags fraud, it's correct 95% of the time on a balanced dataset). If the system flags a live transaction in production, what is the actual probability that it is fraudulent? Explain your reasoning."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Identifying the Base Rate Fallacy:** 
   - Immediately recognize that the "95% Precision on a balanced dataset" is a trap. In the real world, the data is completely unbalanced (99.9% legitimate). 
   - The candidate must explicitly state that the **Base Rate (Prior)** overwhelms the accuracy of the test.
2. **Executing the Math (Mental or Whiteboard):**
   - Out of 10,000 transactions, 10 are actually fraud (0.1%).
   - The model catches 99% of them: roughly 10 true positives.
   - The remaining 9,990 transactions are legitimate.
   - The model has a 5% false positive rate (100% - 95% precision). It will incorrectly flag 5% of the 9,990 legitimate transactions: $9,990 \times 0.05 \approx 500$ false positives!
   - Total flagged transactions = 10 (True) + 500 (False) = 510.
   - The actual probability of fraud if flagged is $\frac{10}{510}$, which is less than **2%**!
3. **Communicating to Stakeholders:** 
   - Explain that despite the model being "highly accurate" on paper, it is practically useless in production because the operations team will be investigating 500 innocent customers for every 10 real fraudsters. 
   - Suggest the engineering fix: Tune the model's prediction threshold to heavily prioritize minimizing False Positives over maximizing Recall.

---
**Task for the end of the day:** Commit your code to Git. Read over the new definitions in the `day_0_prerequisites_and_notation.md` dictionary. 

Tomorrow, in **Day 9**, we take these raw probabilities and organize them into **Probability Distributions** (Gaussian, Binomial) to understand how the universe structures randomness!
