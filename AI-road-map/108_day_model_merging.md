# Day 108: Model Merging (TIES, DARE & Task Vectors)

Welcome to Day 108. 

Imagine you take `LLaMA-3-8B-Base` and fine-tune it on Medical Text. You spend \$5,000 on GPU compute.
Your colleague takes the exact same base model and fine-tunes it on Python Coding. They spend \$5,000.
Your startup now wants an <abbr title="Artificial Intelligence">AI</abbr> that knows *both* Medicine and Coding. Do you have to mix the datasets together and spend \$10,000 to retrain a new model from scratch?

No. Today, we learn the dark magic of **Model Merging**. We will literally mathematically merge the weights of the two neural networks together, combining their intelligence for $0.00!

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Task Vectors (The Math of Knowledge)
When you fine-tune a base model, the weights change slightly. 
If we subtract the Base weights from the Fine-Tuned weights, we get a $\Delta W$ matrix called a **Task Vector**:
$\tau_{medical} = W_{medical} - W_{base}$
This vector represents the pure mathematical "essence" of medical knowledge!

### 2. Linear Interpolation (SLERP)
Can we just average the two models? $W_{merged} = 0.5 \times W_{medical} + 0.5 \times W_{coding}$.
Yes, but doing this purely linearly often destroys the model's geometry.
Instead, researchers use **SLERP (Spherical Linear Interpolation)**. SLERP averages the weights along a high-dimensional spherical curve, preserving the angle and magnitude of the neural pathways much better than a straight average!

### 3. The Interference Problem
What if we want to merge 5 models? 
Model A wants the neuron $w_1$ to go UP by $+0.8$. Model B wants it to go DOWN by $-0.6$. 
If we average them, they cancel each other out to nearly $0.0$. The models destroy each other's knowledge. This is called **Catastrophic Interference**.

### 4. TIES-Merging & DARE (The Breakthroughs)
To solve interference, researchers invented two brilliant algorithms:
- **TIES (Trimming, Electing, Disjoint Merge):** First, we *Trim* (delete) the smallest $20\%$ of weight changes (they are just noise). Then, we *Elect* a sign direction. If 3 models want a weight to be positive, and 2 want it negative, the majority wins! We delete the negative updates entirely, forcing the models to pull in the same direction!
- **DARE (Drop And Rescale):** We randomly drop $90\%$ of the fine-tuned delta weights (reset them to zero!), and mathematically scale up the remaining $10\%$. Surprisingly, the model retains 100% of its knowledge, but frees up $90\%$ of its mathematical space to perfectly merge with other models!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

In production, nobody writes the merging algorithms from scratch. We use the incredible open-source library **MergeKit**.
However, to truly understand it, let's conceptually build **Task Vector Arithmetic** in pure PyTorch!

Create a file named `model_merging.py`:

```python
import torch

def create_task_vector(base_weights, finetuned_weights):
    """
    Extracts the pure 'knowledge' learned during fine-tuning.
    """
    return finetuned_weights - base_weights

def apply_task_vector(base_weights, task_vector, scaling_coefficient=1.0):
    """
    Applies the knowledge back onto the base model.
    Scaling allows you to control how 'strong' the personality is!
    """
    return base_weights + (scaling_coefficient * task_vector)

def ties_elect_sign(task_vector_a, task_vector_b):
    """
    A simplified version of TIES 'Elect' phase.
    If the two models disagree on the direction of a weight update, we force a consensus!
    """
    # 1. Sum the vectors to find the dominant direction
    summed = task_vector_a + task_vector_b
    
    # 2. Get the sign of the dominant direction (+1, -1, or 0)
    majority_sign = torch.sign(summed)
    
    # 3. Force both vectors to ONLY keep weights that match the majority sign!
    # If a weight disagrees, we zero it out!
    resolved_a = torch.where(torch.sign(task_vector_a) == majority_sign, task_vector_a, torch.zeros_like(task_vector_a))
    resolved_b = torch.where(torch.sign(task_vector_b) == majority_sign, task_vector_b, torch.zeros_like(task_vector_b))
    
    return resolved_a, resolved_b

def test_merging():
    print("--- RUNNING MODEL MERGING MATH ---\n")
    
    # 1. The Base Model (Mocking a single weight tensor)
    W_base = torch.tensor([1.0, 1.0, 1.0, 1.0])
    print(f"Base Weights: {W_base.tolist()}")
    
    # 2. Two Fine-Tuned Models
    # Notice the 3rd weight: Medical wants it high (1.8), Coding wants it low (0.4)
    W_medical = torch.tensor([1.5, 1.2, 1.8, 1.1])
    W_coding  = torch.tensor([1.4, 1.1, 0.4, 1.8])
    
    # 3. Extract Task Vectors!
    tau_medical = create_task_vector(W_base, W_medical)
    tau_coding = create_task_vector(W_base, W_coding)
    print(f"Medical Task Vector:  {tau_medical.tolist()}")
    print(f"Coding Task Vector:   {tau_coding.tolist()}\n")
    
    # 4. Naive Addition (Catastrophic Interference on the 3rd weight!)
    naive_sum = tau_medical + tau_coding
    print(f"Naive Sum Vector:     {naive_sum.tolist()}  <-- Notice the 3rd weight is almost 0! Knowledge destroyed!\n")
    
    # 5. TIES Consensus Merging
    print("Applying TIES Consensus...")
    resolved_med, resolved_code = ties_elect_sign(tau_medical, tau_coding)
    print(f"Resolved Med Vector:  {resolved_med.tolist()}")
    print(f"Resolved Code Vector: {resolved_code.tolist()}")
    
    ties_sum = resolved_med + resolved_code
    print(f"TIES Sum Vector:      {ties_sum.tolist()} <-- Notice the disagreement was resolved!\n")
    
    # 6. Apply to Base Model
    W_super_model = apply_task_vector(W_base, ties_sum, scaling_coefficient=0.5)
    print(f"Final Merged 'Super Model' Weights: {W_super_model.tolist()}")

if __name__ == "__main__":
    test_merging()
```

### Key Takeaways from Code:
1. **Task Vector Subtraction:** You can actually take a "Toxic" model, extract its task vector, and *subtract* it from your model to mathematically force the model to be safe! This is called "Unlearning".
2. **The TIES Magic:** Notice how in the Naive sum, the 3rd weight update became `0.2` (canceling out). In the TIES sum, the algorithm realized the Medical vector (+0.8) was stronger than the Coding vector (-0.6). It forced the positive direction, making the final update `0.8`!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: MergeKit YAML
The `MergeKit` library allows you to merge models without writing python code; you just define a YAML configuration file.
**Your Task:**
1. Research the `MergeKit` GitHub repository.
2. Write a `merge.yml` file that merges three models: `mistral-math`, `mistral-code`, and `mistral-writing`.
3. Configure the `merge_method: ties` and specify `density: 0.5` (meaning we drop 50% of the weights).

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Model merging allows us to combine models without retraining. However, when does it fail, and what are the catastrophic interference limits? Finally, what are the <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>/licensing implications of merging models from different companies?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Core Requirement:** 
   - State that you cannot merge LLaMA with Mistral. Model merging strictly requires that all models share the exact same original *Base Architecture and Base Weights*.
2. **Catastrophic Interference Limits:**
   - Explain that if you merge 2 models, Linear/SLERP interpolation works fine. If you merge 10 models, the mathematical space becomes too saturated. The updates destroy each other. You must use TIES or DARE to aggressively prune/drop weights before summing them.
3. **Licensing/<abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> Implications:**
   - Explain that merging a permissively licensed model (Apache 2.0) with a restrictively licensed model (e.g., Llama-3 Community License) "taints" the weights. The resulting merged model inherits the most restrictive license of its parents. You cannot launder <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> through mathematical averaging!

---
**Task for the end of the day:** Commit your code to Git. 

Model merging is amazing, but it has limits. If you need the model to learn 100,000 pages of highly specialized medical literature, you cannot just SFT or Merge it. 

Tomorrow, in **Day 109**, we learn **Continued Pre-Training (CPT) and Domain Adaptation**. We will inject raw, massive knowledge directly into the brain of the <abbr title="Large Language Model">LLM</abbr>!
