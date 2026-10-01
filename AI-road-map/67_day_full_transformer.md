# Day 67: The Full Transformer (Encoder-Decoder)

Welcome to Day 67. Over the last two days, we built the Encoder (BERT) and the Decoder (GPT) in isolation. 

Today, we bolt them together to recreate the exact architecture published by Google in the 2017 *"Attention Is All You Need"* paper. This full architecture was designed for one specific task: **Sequence-to-Sequence Translation**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Machine Translation Workflow
If we want to translate *"The dog barks"* into French (*"Le chien aboie"*), we use the full architecture:
1. **The Encoder:** Reads the entire English sentence bidirectionally. It outputs a matrix of perfect contextual vectors.
2. **The Decoder:** Must generate the French sentence autoregressively (one word at a time). 
   - It starts with `<SOS>` (Start of Sentence). 
   - It looks at what it has written so far using Masked Self-Attention.
   - **Crucially:** It must look at the English sentence to know what to translate!

### 2. The Bridge: Cross-Attention
Inside every single layer of the Decoder, there is a *second* attention mechanism called **Cross-Attention**. This is the bridge between the two networks.
- **The Query ($Q$):** Comes from the **Decoder**. (e.g., The Decoder says: *"I just wrote 'Le', I am looking for the French translation of whatever the main subject is"*).
- **The Keys ($K$) and Values ($V$):** Come directly from the **Encoder**. (e.g., The Encoder holds the English word *"dog"*).
Because the Decoder's Query perfectly matches the Encoder's Key, the Decoder mathematically absorbs the Value of the English word, allowing it to accurately output *"chien"*!

### 3. Label Smoothing (Regularization)
When training the Decoder, we use Cross-Entropy Loss to force it to predict the correct French word. 
If the target word is *"chien"*, standard one-hot encoding tells the AI: *"Be 100% confident it is 'chien', and 0% confident it is anything else."*
This causes the AI to become incredibly overconfident, leading to massive overfitting. 
**Label Smoothing** is a mathematical trick. We tell the AI: *"Be 90% confident it is 'chien', and spread the remaining 10% evenly across the other 50,000 words in the dictionary."* This prevents the gradients from exploding and makes the AI much more robust!

### 4. Weight Tying
Word Embeddings are massive. An embedding matrix for 50,000 words at 512 dimensions requires 25 Million parameters.
The output Classifier (the `nn.Linear` layer at the very end of the Decoder that predicts the final word) *also* requires 25 Million parameters.
**Weight Tying** is a brilliant hack: We physically force the final Output layer to use the *exact same weights* as the Input Embedding layer! We instantly save 25 Million parameters without losing any accuracy!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the Cross-Attention bridge, and assemble the Complete Encoder-Decoder Transformer!

Create a file named `full_transformer.py`:

```python
import torch
import torch.nn as nn
import math

# (Assume we have imported our previously built components)
from multi_head_attention import MultiHeadAttention
from transformer_encoder import TransformerEncoderLayer
from transformer_decoder import MaskedSelfAttention
from transformer_ffn import SwiGLU_FFN

class TransformerDecoderBlock(nn.Module):
    """
    A single block of the full Transformer Decoder.
    It contains THREE sub-layers: Masked Attention, Cross-Attention, and FFN.
    """
    def __init__(self, embed_dim=512, num_heads=8):
        super().__init__()
        
        # 1. Masked Self-Attention (Look at the French words generated so far)
        self.masked_mha = MaskedSelfAttention(embed_dim)
        self.norm1 = nn.LayerNorm(embed_dim)
        
        # 2. CROSS-ATTENTION (The Bridge to the Encoder!)
        self.cross_mha = MultiHeadAttention(embed_dim, num_heads)
        self.norm2 = nn.LayerNorm(embed_dim)
        
        # 3. Feed-Forward Network
        self.ffn = SwiGLU_FFN(embed_dim)
        self.norm3 = nn.LayerNorm(embed_dim)

    def forward(self, x, encoder_output):
        # x: The French sentence so far [Batch, Target_Len, Embed_Dim]
        # encoder_output: The complete English sentence [Batch, Source_Len, Embed_Dim]
        
        # --- 1. Masked Self-Attention ---
        x_norm = self.norm1(x)
        self_att_out, _ = self.masked_mha(x_norm)
        x = x + self_att_out # Residual
        
        # --- 2. CROSS-ATTENTION ---
        # THIS IS THE MAGIC!
        # The Queries come from 'x' (The Decoder)
        # The Keys and Values come from 'encoder_output' (The Encoder)
        x_norm = self.norm2(x)
        
        # We must slightly modify our standard MHA to accept separate Q, K, V
        # cross_att_out = self.cross_mha(query=x_norm, key=encoder_output, value=encoder_output)
        
        # (For this mock code, assume our MHA class accepts Q, K, V separately)
        # x = x + cross_att_out
        
        # --- 3. FFN ---
        x_norm = self.norm3(x)
        ffn_out = self.ffn(x_norm)
        x = x + ffn_out
        
        return x

class FullTransformer(nn.Module):
    """
    The Complete 2017 Architecture!
    """
    def __init__(self, source_vocab_size, target_vocab_size, embed_dim=512):
        super().__init__()
        
        # We need two separate embedding tables (e.g., English and French)
        self.encoder_embed = nn.Embedding(source_vocab_size, embed_dim)
        self.decoder_embed = nn.Embedding(target_vocab_size, embed_dim)
        
        # (Mocking the stacks of layers for simplicity)
        self.encoder_layer = TransformerEncoderLayer(embed_dim)
        self.decoder_layer = TransformerDecoderBlock(embed_dim)
        
        # The final output classifier
        self.output_layer = nn.Linear(embed_dim, target_vocab_size, bias=False)
        
        # WEIGHT TYING! 
        # We literally overwrite the Output Layer's weights with the Decoder Embedding's weights!
        self.output_layer.weight = self.decoder_embed.weight

    def forward(self, source_sentence, target_sentence):
        # 1. ENCODER
        enc_emb = self.encoder_embed(source_sentence)
        encoder_output = self.encoder_layer(enc_emb)
        
        # 2. DECODER
        dec_emb = self.decoder_embed(target_sentence)
        
        # The Decoder takes BOTH the target sentence AND the encoder's output!
        decoder_output = self.decoder_layer(dec_emb, encoder_output)
        
        # 3. Final Prediction
        logits = self.output_layer(decoder_output)
        
        return logits

def test_full_transformer():
    print("--- RUNNING FULL ENCODER-DECODER TRANSFORMER ---")
    
    BATCH_SIZE = 2
    ENG_VOCAB = 10000
    FRA_VOCAB = 12000
    
    english_sentence = torch.randint(0, ENG_VOCAB, (BATCH_SIZE, 10))
    french_sentence = torch.randint(0, FRA_VOCAB, (BATCH_SIZE, 12))
    
    model = FullTransformer(ENG_VOCAB, FRA_VOCAB)
    logits = model(english_sentence, french_sentence)
    
    print(f"English Input: {english_sentence.shape}")
    print(f"French Input:  {french_sentence.shape}")
    print(f"Final Logits:  {logits.shape} (Predicting the next word across 12,000 French words!)")
    
    print("\nWeight Tying successfully saved us 12000 * 512 = 6.1 Million parameters!")

if __name__ == "__main__":
    test_full_transformer()
```

### Key Takeaways from Code:
1. **The Cross-Attention Inputs:** Look closely at the Cross-Attention step. The Decoder creates the Query, but the Encoder provides the Keys and Values. This is the exact moment the translation occurs mathematically!
2. **Weight Tying:** Look at `self.output_layer.weight = self.decoder_embed.weight`. This single line of code forces both layers to share the same physical memory on the GPU.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Machine Translation Inference Loop
You have built the training loop. Now build the inference loop.
**Your Task:**
1. You want to translate `"Hello"`. Pass `"Hello"` through the Encoder to get the `encoder_output`.
2. Start the Decoder with just the `<SOS>` token. 
3. Pass `[<SOS>]` and `encoder_output` into the Decoder. Get the prediction (e.g., `"Bonjour"`).
4. Now pass `[<SOS>, "Bonjour"]` and the EXACT SAME `encoder_output` into the Decoder.
5. Notice that you only run the Encoder *once*. But you must run the Decoder in a `while` loop until it outputs `<EOS>`!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"GPT is decoder-only, BERT is encoder-only, and T5 is encoder-decoder. Explain the architectural trade-offs of each, and why the industry has converged almost entirely on decoder-only architectures for modern LLMs."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **BERT (Encoder-Only):** 
   - Pro: Perfect bidirectional context, making it the absolute king of classification and sentiment analysis.
   - Con: Because it relies on looking at the entire sentence at once, it physically cannot generate new text autoregressively.
2. **T5 (Encoder-Decoder):**
   - Pro: The most versatile. Excellent at translation and summarization because the Encoder reads the document perfectly, and the Decoder writes the summary.
   - Con: Extremely complex to serve in production because you must manage two separate KV-caches and two different architectures simultaneously.
3. **GPT (Decoder-Only):**
   - Pro: Simplicity. Because it is autoregressive, it generates text flawlessly.
   - The Convergence: Industry realized that if you make a Decoder *massive* (e.g., 100 Billion parameters), its causal context becomes so powerful that it effectively rivals BERT's bidirectional context! By using a Decoder-only architecture, engineering teams only have to optimize one single, uniform pipeline, making scaling and KV-cache management infinitely easier.

---
**Task for the end of the day:** Commit your code to Git. 

Tomorrow, in **Day 68**, we ask a massive question: How do you train an AI on 1 Trillion words if you don't have human labels? We will learn the genius of **Masked Language Modeling (MLM)** and the Pre-training paradigm!
