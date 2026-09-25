# Day 33: Backpropagation & Computational Graphs

Welcome to Day 33. This is it. This is the hardest math in all of Artificial Intelligence. 
Today, we answer the ultimate question: **How does a Neural Network actually learn?**

The answer is **Backpropagation**. It is the mathematical engine of every <abbr title="Artificial Intelligence">AI</abbr> on earth, from a simple Perceptron to ChatGPT.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Forward Pass
Imagine water flowing through pipes. The input data (e.g., an image of a dog) enters the network. It flows forward through the Weights, through the Activation Functions, layer by layer, until it reaches the end. The <abbr title="Artificial Intelligence">AI</abbr> shouts: *"It's a Cat!"*
This is the **Forward Pass**. It is just simple multiplication.

### 2. The Loss
The <abbr title="Artificial Intelligence">AI</abbr> guessed Cat (0), but the true answer was Dog (1). 
We use a Loss Function to calculate exactly how wrong the <abbr title="Artificial Intelligence">AI</abbr> was. (e.g., Error = 100).

### 3. Backpropagation (The Chain Rule)
Now the magic happens. We must send that Error of 100 *backward* through the pipes, so every single Weight can adjust itself.
How much should Weight #1 adjust? How much should Weight #85 adjust? 
We use the **Calculus Chain Rule**. 
$$ \frac{\partial Loss}{\partial Weight} = \frac{\partial Loss}{\partial Output} \times \frac{\partial Output}{\partial Hidden} \times \frac{\partial Hidden}{\partial Weight} $$
In plain English: "How much did this specific weight contribute to the final error?" 
The math calculates the exact partial derivative (slope) for every single weight in the entire network, telling them exactly how much to shift (e.g., "Weight 1, go up by 0.05. Weight 2, go down by 0.12").

### 4. Computational Graphs & Autograd
If you had a 100-layer network, writing that Calculus equation by hand would take a human 50 years. 
PyTorch solves this using **Computational Graphs**.
Every time you multiply two numbers in PyTorch, it silently draws a "Node" in the <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> of your computer, keeping a physical roadmap of the math. 
When you type `.backward()`, the **Autograd** engine just walks backward along the graph. Because it knows the derivative of addition is 1, and the derivative of multiplication is the other number, it instantly calculates the exact calculus without you writing a single equation!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

To truly understand Autograd, we are going to build a micro-version of PyTorch entirely from scratch. We will create a `Value` object that remembers its own math and calculates its own backward derivative. *(This exercise is heavily inspired by Andrej Karpathy's brilliant 'micrograd' tutorial).*

Create a file named `micro_autograd.py`:

```python
import numpy as np

class Value:
    """A single number that remembers the mathematical operation that created it!"""
    def __init__(self, data, _children=(), _op='', label=''):
        self.data = data
        self.grad = 0.0  # The derivative (slope). Starts at 0.
        self._backward = lambda: None # Function to calculate the backward calculus
        self._prev = set(_children) # Remember the parent numbers
        self._op = _op   # Remember the operation (+, *)
        self.label = label

    def __repr__(self):
        return f"Value(data={self.data}, grad={self.grad}, label={self.label})"

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), '+')

        def _backward():
            # Calculus Rule: The derivative of Addition routes 1.0 to both parents!
            self.grad += 1.0 * out.grad
            other.grad += 1.0 * out.grad
        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), '*')

        def _backward():
            # Calculus Rule: The derivative of Multiplication is the OTHER number!
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out

def run_autograd():
    print("--- BUILDING THE COMPUTATIONAL GRAPH ---")
    
    # 1. Inputs (Data)
    x = Value(2.0, label='x')
    y = Value(-3.0, label='y')
    
    # 2. Weights
    w1 = Value(0.5, label='w1')
    w2 = Value(1.0, label='w2')
    
    # 3. The Forward Pass (Math)
    # This automatically builds the graph in memory!
    hidden1 = x * w1; hidden1.label = 'hidden1'
    hidden2 = y * w2; hidden2.label = 'hidden2'
    output = hidden1 + hidden2; output.label = 'output'
    
    print(f"Forward Pass Output: {output.data}") # Should be (2*0.5) + (-3*1.0) = -2.0
    
    # 4. THE BACKWARD PASS!
    print("\n--- TRIGGERING BACKPROPAGATION ---")
    # The derivative of the output to itself is always 1
    output.grad = 1.0 
    
    # Manually walk backward through the graph!
    output._backward()
    hidden1._backward()
    hidden2._backward()
    
    print(x)
    print(w1)
    print(y)
    print(w2)
    print("Notice how w1 got a gradient of 2.0 (which was the value of x).")
    print("This is the exact mechanic underlying PyTorch's .backward() function!")

if __name__ == "__main__":
    run_autograd()
```

### Key Takeaways from Code:
1. **Memory of Math:** The `Value` class is the secret to deep learning. When we add two numbers, the output object literally saves a pointer to `self` and `other`. It builds a tree.
2. **Local Derivatives:** Look at the `_backward` function inside `__mul__`. It doesn't need to know the massive Chain Rule for 100 layers. It only knows its *local* calculus rule: "Multiply the incoming gradient by the other number." When 100 nodes do their local rule backward in a line, the entire Calculus Chain Rule completes perfectly!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Adding ReLU to Autograd
Our `Value` class currently supports Addition and Multiplication. 
**Your Task:**
1. Add a new method inside the `Value` class called `def relu(self):`.
2. The forward pass is easy: `out = Value(0 if self.data < 0 else self.data, (self,), 'ReLU')`.
3. You must write the `_backward` function for it.
4. *Hint:* What is the local derivative of ReLU? If the output was $> 0$, the gradient passes perfectly through ($1.0 \times out.grad$). If the output was $<= 0$, the gradient becomes $0.0$.
5. Test it by passing a negative number through your graph and verifying the gradient gets killed!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"PyTorch's Autograd engine uses Reverse-Mode Automatic Differentiation (Backpropagation). When would Forward-Mode AD be mathematically more efficient? Discuss the Jacobian shape argument."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Reverse-Mode AD (PyTorch):** 
   - State that Deep Learning usually has massive inputs (like an Image with 1,000,000 pixels) mapping down to a single output (1 Loss number). 
   - Reverse-mode AD starts at the 1 output and works backward. Because there is only 1 output, it calculates all 1,000,000 gradients in a single sweep!
2. **Forward-Mode AD:**
   - Explain that Forward-Mode starts at the Inputs and works forward.
   - If we have 1,000,000 inputs, Forward-Mode requires us to run the graph 1,000,000 separate times (once for each input)! This is why PyTorch doesn't use it.
3. **The Jacobian Shape:**
   - Conclude that if you had a bizarre mathematical problem with 3 inputs and 10,000 outputs, Forward-Mode would suddenly be much faster. 
   - In short: Reverse-mode is for mapping Many-to-One. Forward-mode is for mapping One-to-Many.

---
**Task for the end of the day:** Commit your code to Git. You have successfully implemented the engine of <abbr title="Artificial Intelligence">AI</abbr>.

Tomorrow, in **Day 34**, we learn the first step of actually building a network: **Weight Initialization (Xavier & Kaiming).** If you start your network with the wrong numbers, the math will instantly explode!
