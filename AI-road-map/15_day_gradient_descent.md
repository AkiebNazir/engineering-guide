# Day 15: Gradient Descent from First Principles

Welcome to Day 15! Today marks the beginning of **Phase 3: Optimization Theory**. 

For the past two weeks, we defined the "Loss" of a model (how many mistakes it makes) using Calculus and Probability. But knowing *how many* mistakes you made doesn't fix the model. We need an algorithm that actually updates the Neural Network's weights to make it smarter.

That algorithm is **Gradient Descent**. It is the engine that powers every single modern AI, from linear regression models to GPT-4. Today, we build that engine from scratch.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. Convex vs. Non-Convex Functions
Before we optimize, we have to look at the mathematical landscape of our errors (the Loss Landscape).
- **Convex Function:** A mathematical landscape shaped like a perfect, smooth bowl. It is mathematically guaranteed to have exactly one bottom (the **Global Minimum**). Linear Regression has a convex loss landscape.
- **Non-Convex Function:** A chaotic landscape full of jagged hills, deep valleys, and false bottoms. These false bottoms are called **Local Minima**. Deep Neural Networks produce highly non-convex landscapes, which is why they are incredibly difficult to train.

### 2. The Gradient Descent Update Rule
Gradient Descent is an algorithm that starts at a random point on the mountain, looks at the slope (the derivative) beneath its feet, and takes a step exactly downhill.

**The Golden Equation of Machine Learning:**
$$ \theta_{t+1} = \theta_t - \eta \nabla_\theta \mathcal{L}(\theta_t) $$

Where:
- $\theta_t$: Your current weights (where you are standing right now).
- $\nabla_\theta \mathcal{L}(\theta_t)$: The **Gradient** (a vector pointing directly *uphill* toward the steepest slope).
- $-$: The minus sign. We subtract the gradient because we want to go *downhill*, not uphill!
- $\eta$ (Eta): The **Learning Rate**. This scales the gradient. It decides how big of a step we take.
- $\theta_{t+1}$: Your new, smarter weights after taking the step.

### 3. Convergence Conditions & The Learning Rate ($\eta$)
The **Learning Rate** is the single most important hyperparameter in AI.
- **Too Large:** You take a massive step, overshoot the bottom of the valley entirely, and bounce up the other side. The model "explodes."
- **Too Small:** You take microscopic baby steps. The model might take 5,000 years to reach the bottom.
- **Just Right:** The model smoothly glides to the bottom in minimal steps.

### 4. Lipschitz Continuity & Convergence Rate
How do we mathematically guarantee that Gradient Descent won't explode? We rely on **Lipschitz Continuity**. 
This is a mathematical property that states: *"The slope of this mountain will never suddenly spike to infinity."* 
If the Loss function is Lipschitz continuous, and it is a Convex bowl, mathematicians have proven that Gradient Descent has a convergence rate of $O(1/T)$. This means if you want the error to get 10x smaller, you must run 10x more training steps.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's write a pure Python implementation of Gradient Descent to solve a Linear Regression problem. We will also implement **Learning Rate Schedules**, which dynamically change the size of the step as the model gets closer to the bottom of the valley.

Create a file named `gradient_descent.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def generate_data():
    """Generates synthetic data for Linear Regression: y = 2x + 1"""
    X = np.random.rand(100, 1) * 10
    # Add Gaussian noise
    y = 2 * X + 1 + np.random.randn(100, 1) * 2
    return X, y

def gradient_descent(X, y, learning_rate=0.01, iterations=50, schedule="constant"):
    """
    Performs Gradient Descent to find the best line (Weights & Bias).
    Formula: y = Wx + b
    """
    print(f"--- RUNNING GRADIENT DESCENT (Schedule: {schedule}) ---")
    
    m = len(y)
    # 1. Start with terrible random guesses
    W = np.random.randn(1, 1)
    b = np.random.randn(1)
    
    history_W = []
    history_b = []
    history_loss = []
    
    initial_lr = learning_rate
    
    for i in range(iterations):
        # Forward Pass: Make a prediction
        y_pred = X.dot(W) + b
        
        # Calculate Loss (Mean Squared Error)
        loss = (1/(2*m)) * np.sum((y_pred - y)**2)
        
        # Record history for plotting
        history_W.append(W[0][0])
        history_b.append(b[0])
        history_loss.append(loss)
        
        # Calculate Gradients (Calculus derivatives of MSE)
        dW = (1/m) * np.sum((y_pred - y) * X)
        db = (1/m) * np.sum(y_pred - y)
        
        # --- LEARNING RATE SCHEDULES ---
        if schedule == "step" and i % 10 == 0 and i > 0:
            learning_rate = learning_rate * 0.5 # Cut LR in half every 10 steps
        elif schedule == "exponential":
            learning_rate = initial_lr * np.exp(-0.05 * i)
            
        # The Golden Equation! Take the step downhill.
        W = W - learning_rate * dW
        b = b - learning_rate * db
        
    print(f"Final Weights -> W: {W[0][0]:.3f} (True: 2.0), b: {b[0]:.3f} (True: 1.0)")
    print(f"Final Loss: {loss:.3f}\n")
    return history_W, history_b, history_loss

def plot_loss_surface(X, y, history_W, history_b, history_loss):
    """Visualizes the 3D Convex Loss Bowl and the path our algorithm took."""
    # Create a grid of possible W and b values
    W_vals = np.linspace(-1, 5, 50)
    b_vals = np.linspace(-3, 5, 50)
    W_grid, b_grid = np.meshgrid(W_vals, b_vals)
    Loss_grid = np.zeros_like(W_grid)
    
    # Calculate exact loss for every combination to draw the bowl
    m = len(y)
    for i in range(len(W_vals)):
        for j in range(len(b_vals)):
            y_pred = X * W_grid[i, j] + b_grid[i, j]
            Loss_grid[i, j] = (1/(2*m)) * np.sum((y_pred - y)**2)
            
    # 3D Plotting
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot the transparent bowl
    ax.plot_surface(W_grid, b_grid, Loss_grid, cmap='viridis', alpha=0.5)
    
    # Plot the path Gradient Descent took!
    ax.plot(history_W, history_b, history_loss, color='red', marker='o', 
            markersize=4, linewidth=2, label='Gradient Descent Path')
    
    ax.set_xlabel('Weight (W)')
    ax.set_ylabel('Bias (b)')
    ax.set_zlabel('Loss (Error)')
    ax.set_title('Gradient Descent sliding down the Convex Loss Bowl')
    ax.legend()
    
    filename = "gd_loss_surface.png"
    plt.savefig(filename)
    print(f"Saved 3D visualization to {filename}. Watch it slide to the bottom!")

if __name__ == "__main__":
    X, y = generate_data()
    
    # Run with a constant learning rate
    w_hist, b_hist, l_hist = gradient_descent(X, y, learning_rate=0.05, schedule="constant")
    
    # Run with an exponential decay schedule
    gradient_descent(X, y, learning_rate=0.1, schedule="exponential")
    
    plot_loss_surface(X, y, w_hist, b_hist, l_hist)
```

### Key Takeaways from Code:
1. **The Gradient Calculations:** Look at `dW` and `db`. Notice they multiply the raw error `(y_pred - y)` by the input `X`. If the error is large, the gradient is large. As the error shrinks near the bottom of the bowl, the gradient naturally shrinks, helping the model gently settle into the Global Minimum without overshooting!
2. **Learning Rate Schedules:** Sometimes we want to start with a huge step to get off a plateau quickly, but then switch to microscopic baby steps to perfectly land in the exact center of the valley. By dynamically shrinking $\eta$ using a `schedule`, we get the best of both worlds.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Rosenbrock Torture Test
**Your Task:** Create a file named `rosenbrock_gd.py`.

The **Rosenbrock Function** is a famous mathematical equation shaped like a curved, narrow valley (a banana). It is explicitly designed to confuse Optimization algorithms.
The equation is: $f(x, y) = (a - x)^2 + b(y - x^2)^2$ (where $a=1, b=100$).
The Global Minimum is exactly at $(1, 1)$, but the valley leading to it is incredibly flat.

1. Write a function that calculates the Rosenbrock value given $x$ and $y$.
2. Write a function that calculates the gradients. (You will need to compute the partial derivatives $\frac{\partial f}{\partial x}$ and $\frac{\partial f}{\partial y}$ by hand on paper first!).
3. Implement Gradient Descent to optimize it. 
4. **The Catch:** Try a learning rate of $0.01$. Your algorithm will explode to infinity. Try $0.0001$. It will take 10,000 steps to move an inch. You must find the exact learning rate balance to survive the banana!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Why is the choice of Learning Rate considered the single most important hyperparameter in Deep Learning? Furthermore, if I double my Batch Size (the amount of data processed per step) during training, what should I theoretically do to my Learning Rate, and why does this affect how well the model generalizes to unseen data?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Why it is the most important:** 
   - State that if the learning rate is too high, the model diverges (explodes to NaN). If it is too low, the model gets permanently stuck in Local Minima or saddle points and never converges. It literally dictates whether the network trains at all.
2. **The Batch Size Relationship (Linear Scaling Rule):**
   - Explain that if you double the Batch Size, your gradient estimation becomes twice as stable/accurate (because you averaged over twice as much data).
   - Therefore, because you trust your compass direction twice as much, you should theoretically **double the Learning Rate** to take a bigger, faster step. (This is known as the *Linear Scaling Rule*).
3. **Generalization (The Flat Minima Theory):**
   - Note that using a small batch size creates a very "noisy" gradient. This chaotic noise is actually a good thing—it bumps the model out of "sharp" local valleys and forces it to settle in "wide, flat" valleys. 
   - State that models in wide, flat valleys generalize much better to unseen test data because a slight shift in the data doesn't cause a massive spike in error. Therefore, pushing batch sizes too high can actually degrade real-world performance!

---
**Task for the end of the day:** Commit your code to Git. Look at your 3D plot and marvel at how simple calculus equations can find the mathematical center of the universe.

Tomorrow, in **Day 16**, we realize that calculating the gradient for 1 million data points per step is far too slow. We will introduce **Stochastic Gradient Descent (SGD)** and add intentional noise to the system!
