# Day 64: Feed-Forward Network & Layer Norm

Welcome to Day 64. The Multi-Head Attention mechanism is incredible. It allows words to bond with other words, routing context across a sentence perfectly. 
But Attention is basically just a complex sorting mechanism. It doesn't actually "think". 

The actual factual knowledge of the <abbr title="Artificial Intelligence">AI</abbr>—the part that knows that Paris is the capital of France—is stored inside the **Position-wise Feed-Forward Network (FFN)**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Position-wise FFN
After the 512-dimensional vector emerges from the Attention block, it is passed into an FFN. 
- **Position-wise:** This means the FFN looks at every word completely *independently*. At this point, the word "Bank" already contains the context of "River". The FFN just looks at the single 512D vector for "Bank" and processes it.
- **The Expansion:** The FFN first passes the 512D vector into a massive `nn.Linear` layer that blows it up to $2048$ dimensions! It applies an Activation Function, and then uses a second `nn.Linear` layer to crush it back down to $512$ dimensions.
- **Why?** This massive 2048D expansion gives the Neural Network a massive amount of parameters (memory) to store facts, logic, and reasoning!

### 2. The SwiGLU Upgrade
In 2017, the Transformer used a simple ReLU activation function. 
Modern models (LLaMA, PaLM) use **SwiGLU** (Swish Gated Linear Unit).
Instead of a standard FFN, SwiGLU creates TWO separate massive neural pathways.
- Pathway A processes the data.
- Pathway B acts as a **Gate**. It uses the Swish activation function to mathematically decide exactly *which* facts in Pathway A should be allowed to pass through, and which should be blocked!
SwiGLU increases the parameter count, but results in a massive leap in <abbr title="Artificial Intelligence">AI</abbr> reasoning capabilities.

### 3. The Stability Crisis: Pre-Norm vs Post-Norm
A Transformer is just an Attention block followed by an FFN block.
To train a 100-layer Transformer without exploding gradients, we must use **Layer Normalization** and **Residual Connections** (from ResNet, Day 39).
- **Post-Norm (2017):** The original paper did this: `Attention(x) -> Add Residual -> LayerNorm`. This is notoriously unstable. If you try to train a 100-layer Post-Norm model, it will crash instantly.
- **Pre-Norm (Modern):** Today, every <abbr title="Large Language Model">LLM</abbr> does this: `LayerNorm(x) -> Attention -> Add Residual`. By normalizing the data *before* it enters the block, the Residual Connection remains completely untouched! This guarantees perfect mathematical stability for models up to 1000 layers deep!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build both the standard 2017 FFN, and the modern SwiGLU FFN used by LLaMA 3. 
We will see how SwiGLU uses a gating mechanism to control information flow!

Create a file named `transformer_ffn.py`:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class StandardFFN(nn.Module):
    """
    The original 2017 Transformer FFN.
    """
    def __init__(self, embed_dim=512, expand_dim=2048):
        super().__init__()
        # Blow it up to 2048
        self.fc1 = nn.Linear(embed_dim, expand_dim)
        # Crush it back to 512
        self.fc2 = nn.Linear(expand_dim, embed_dim)

    def forward(self, x):
        # x shape: [Batch, Seq_Len, 512]
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        return x

class SwiGLU_FFN(nn.Module):
    """
    The modern LLaMA FFN using Gated Linear Units!
    """
    def __init__(self, embed_dim=512, expand_dim=2048):
        super().__init__()
        
        # PATHWAY A: The Data
        self.fc_data = nn.Linear(embed_dim, expand_dim, bias=False)
        
        # PATHWAY B: The Gate!
        self.fc_gate = nn.Linear(embed_dim, expand_dim, bias=False)
        
        # The Final Output Projection
        self.fc_out = nn.Linear(expand_dim, embed_dim, bias=False)

    def forward(self, x):
        # 1. Process the data
        # Shape: [Batch, Seq_Len, 2048]
        data = self.fc_data(x)
        
        # 2. Process the Gate
        gate = self.fc_gate(x)
        
        # 3. Apply the Swish Activation to the Gate
        # Swish(x) = x * sigmoid(x)
        activated_gate = F.silu(gate) 
        
        # 4. THE MULTIPLICATION! (The Gating Mechanism)
        # We multiply the Data by the Gate. If the Gate says 0.0, the data is blocked!
        gated_data = data * activated_gate
        
        # 5. Crush back to 512
        final_output = self.fc_out(gated_data)
        
        return final_output

def test_ffn():
    print("--- RUNNING TRANSFORMER FEED-FORWARD NETWORKS ---")
    
    BATCH_SIZE = 2
    SEQ_LEN = 10
    EMBED_DIM = 512
    
    # Simulate the output of the Attention mechanism
    attention_output = torch.randn(BATCH_SIZE, SEQ_LEN, EMBED_DIM)
    
    # 1. Run Standard FFN
    model_standard = StandardFFN(embed_dim=EMBED_DIM)
    out_standard = model_standard(attention_output)
    
    # 2. Run SwiGLU FFN
    model_swiglu = SwiGLU_FFN(embed_dim=EMBED_DIM)
    out_swiglu = model_swiglu(attention_output)
    
    print(f"Attention Input Shape: {attention_output.shape}")
    print(f"Standard FFN Output:   {out_standard.shape}")
    print(f"SwiGLU FFN Output:     {out_swiglu.shape}")
    
    # Let's count parameters!
    params_standard = sum(p.numel() for p in model_standard.parameters())
    params_swiglu = sum(p.numel() for p in model_swiglu.parameters())
    
    print(f"\nStandard FFN Parameters: {params_standard:,}")
    print(f"SwiGLU FFN Parameters:   {params_swiglu:,}")
    print("\nSwiGLU has exactly 50% more parameters because it requires an entire second network just to control the Gate!")

if __name__ == "__main__":
    test_ffn()
```

### Key Takeaways from Code:
1. **The Swish Activation (`F.silu`):** We use SiLU (Sigmoid Linear Unit, also known as Swish) on the gate. It is a smooth, continuous curve that performs better than the sharp, angular ReLU.
2. **The Parameter Cost:** Look at the `SwiGLU_FFN` class. It has three linear layers instead of two. This means SwiGLU is 50% more expensive to run. To compensate for this, LLaMA physically shrinks the `expand_dim` size (e.g., from 2048 to 1365) to keep the parameter count identical to a standard FFN!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Complete Pre-Norm Block
You now have the two halves of a Transformer layer: Attention and FFN.
**Your Task:**
1. Conceptually create a `TransformerBlock` class.
2. Initialize an `Attention` module, a `SwiGLU` module, and TWO `nn.LayerNorm` modules.
3. Write the `forward` pass using **Pre-Norm** math:
   - `x_norm1 = LayerNorm1(x)`
   - `attention_out = Attention(x_norm1)`
   - `x_add1 = x + attention_out` (Notice the residual adds the original `x`, not the normed `x`!)
   - `x_norm2 = LayerNorm2(x_add1)`
   - `ffn_out = SwiGLU(x_norm2)`
   - `final_out = x_add1 + ffn_out`
4. You have just built a completely mathematically stable LLaMA block!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"In deep Transformer networks, why did the industry abandon Post-Norm in favor of Pre-Norm? Explain the effect on the gradient flow during backpropagation."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Post-Norm Gradient Blockade:** 
   - Explain that in Post-Norm `LayerNorm(x + Sublayer(x))`, the gradient flowing backwards through the network must mathematically pass *through* the LayerNorm derivative at every single layer. 
   - Because LayerNorm scales data based on variance, it severely dampens the gradients. In a 100-layer network, the gradients vanish before reaching Layer 1.
2. **The Pre-Norm Highway:**
   - Explain that in Pre-Norm `x + Sublayer(LayerNorm(x))`, the main residual pathway is `x + y + z + ...`. 
   - Conclude that because there is no LayerNorm on the main pathway, the gradient of an addition is exactly $1.0$. Gradients can flow directly from Layer 100 to Layer 1 via an unobstructed superhighway, guaranteeing mathematical stability at infinite depths!

---
**Task for the end of the day:** Commit your code to Git. 

Tomorrow, in **Day 65**, we take everything we've built over the last 4 days and snap it together like Lego bricks. We will build the complete **Transformer Encoder** (The BERT Architecture)!
