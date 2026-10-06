# Day 82: Multi-Modal Transformers (LLaVA)

Welcome to Day 82. LLMs are blind. They only understand text. But what if we want to show ChatGPT an image of a broken bicycle and ask *"How do I fix this?"*

In Day 71, we built the Vision Transformer (ViT), which treats an image like a sentence of patches. Today, we bolt that ViT directly into an LLM using the **LLaVA (Large Language-and-Vision Assistant)** architecture.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Early Fusion vs Late Fusion
If you want to build a Multi-Modal AI, there are two ways:
- **Early Fusion:** You build a massive architecture from scratch. You feed it 10 Billion images and 1 Trillion words simultaneously. It takes 6 months and $100 Million to train.
- **Late Fusion (The LLaVA Hack):** You take a massive, already-trained Vision model (like CLIP). You take a massive, already-trained Language model (like LLaMA). You literally just glue them together. You only have to train the glue! This takes 3 days and costs $500.

### 2. The LLaVA Architecture
LLaVA is a masterpiece of Late Fusion. Here is the flow:
1. **The Vision Encoder:** You pass an image into a frozen CLIP ViT. It slices the image into patches and outputs 576 patch embeddings. The dimension of these embeddings is 1024.
2. **The Problem:** The LLaMA language model expects text embeddings of dimension 4096. It cannot read dimension 1024.
3. **The Projector (The Glue):** We build a tiny, 2-layer MLP (Multi-Layer Perceptron): `Linear(1024, 4096)`. 
4. **The Translation:** The MLP mathematically projects the 576 visual embeddings into the 4096-dimensional language space. 
5. **The Prompt:** The user types `"<image> What is broken?"`. The Tokenizer finds the `<image>` token, deletes it, and physically inserts the 576 projected ViT embeddings into that exact spot in the sequence!
6. **The LLM:** The LLaMA model processes the sequence. To the LLM, the image just looks like 576 very strange "words" describing a broken bicycle. It autoregressively outputs the fix!

### 3. Two-Stage Training
Because the ViT and the LLM are already intelligent, we FREEZE them both.
1. **Stage 1 (Feature Alignment):** We train *only* the MLP Projector using 500k simple image-caption pairs (e.g., Image of a dog $\rightarrow$ "A brown dog"). The MLP learns to translate "Visual Language" into "English".
2. **Stage 2 (Instruction Tuning):** We unfreeze the LLM (or use LoRA) and train on complex multi-modal conversations (e.g., "Why is this meme funny?"). The LLM learns to reason deeply about the visual tokens!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the glue! We will mock a Vision Encoder and an LLM, and build the LLaVA architecture that connects them.

Create a file named `multimodal_llava.py`:

```python
import torch
import torch.nn as nn

class LLaVA_Projector(nn.Module):
    """
    The tiny "Glue" network that translates Vision into Language.
    Usually a 2-layer MLP with a GELU activation.
    """
    def __init__(self, vision_dim=1024, language_dim=4096):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(vision_dim, language_dim),
            nn.GELU(),
            nn.Linear(language_dim, language_dim)
        )
        
    def forward(self, vision_features):
        return self.mlp(vision_features)

class MockLLaVA(nn.Module):
    """
    The full Multi-Modal Architecture.
    """
    def __init__(self, vision_dim=1024, language_dim=4096):
        super().__init__()
        
        # 1. The Projector (This is the ONLY thing we train in Stage 1!)
        self.projector = LLaVA_Projector(vision_dim, language_dim)
        
        # 2. Mock Language Embedding Layer
        # Assuming vocab size of 32000
        self.text_embedding = nn.Embedding(32000, language_dim)
        
        # 3. Mock LLM (A simple Linear layer representing the massive Transformer)
        self.llm = nn.Linear(language_dim, 32000)

    def forward(self, text_token_ids, vision_features=None, image_token_index=500):
        """
        text_token_ids: [Batch, Seq_Len]
        vision_features: [Batch, Num_Patches, Vision_Dim] (From the frozen ViT)
        image_token_index: The special ID for the <image> token.
        """
        # 1. Embed the text tokens normally
        # Shape: [Batch, Seq_Len, Language_Dim]
        embeddings = self.text_embedding(text_token_ids)
        
        # 2. If we have an image, inject it!
        if vision_features is not None:
            # Translate Vision to Language!
            # Shape: [Batch, Num_Patches, Language_Dim]
            projected_vision = self.projector(vision_features)
            
            # Find WHERE the <image> token is in the text sequence
            # (For simplicity in this mock, we just prepend the image to the text)
            # In real LLaVA, you slice the tensor and insert the image at the exact token index.
            embeddings = torch.cat([projected_vision, embeddings], dim=1)
            
        # 3. Pass the combined embeddings into the LLM!
        logits = self.llm(embeddings)
        return logits

def test_llava():
    print("--- RUNNING LLaVA MULTI-MODAL ARCHITECTURE ---")
    
    BATCH_SIZE = 1
    VISION_DIM = 1024
    LANGUAGE_DIM = 4096
    NUM_PATCHES = 576  # Typical for a 336x336 image with 14x14 patches
    TEXT_SEQ_LEN = 10
    
    # Simulate an image passing through a frozen CLIP model
    mock_vision_features = torch.randn(BATCH_SIZE, NUM_PATCHES, VISION_DIM)
    
    # Simulate a user text prompt: "<image> What is broken?"
    mock_text_ids = torch.randint(0, 32000, (BATCH_SIZE, TEXT_SEQ_LEN))
    
    model = MockLLaVA(vision_dim=VISION_DIM, language_dim=LANGUAGE_DIM)
    
    # Forward Pass!
    output_logits = model(mock_text_ids, vision_features=mock_vision_features)
    
    print(f"Vision Features from CLIP: {mock_vision_features.shape}")
    print(f"Text Token IDs: {mock_text_ids.shape}")
    print(f"Final LLM Input Sequence Length: {NUM_PATCHES + TEXT_SEQ_LEN} tokens!")
    print(f"Output Logits Shape: {output_logits.shape}")
    print("\nThe LLM successfully processed 576 'Image Words' and 10 'Text Words' simultaneously!")

if __name__ == "__main__":
    test_llava()
```

### Key Takeaways from Code:
1. **The Shape Match:** Notice how `projected_vision` and `embeddings` both have the exact same final dimension (`4096`). This is why `torch.cat` works. The Transformer has no idea that the first 576 tokens came from a JPEG file. It just does math!
2. **Context Window Cost:** Images are expensive! 576 tokens is equivalent to a long paragraph of text. If you feed the LLM a 1-minute video at 1 FPS, that's $60 \text{ frames} \times 576 \text{ tokens} = 34,560$ tokens!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: HuggingFace LLaVA
You understand the math. Now use the real thing.
**Your Task:**
1. Mentally design a script using the `transformers` library.
2. Import `LlavaProcessor` and `LlavaForConditionalGeneration`.
3. Use the PIL (Python Imaging Library) to load a JPG image of a receipt.
4. Set the prompt: `"USER: <image>\nExtract the total price from this receipt. ASSISTANT:"`.
5. Pass the image and prompt into the Processor, then into the Model to `.generate()` the answer!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a document understanding system for a Bank that processes PDFs containing text, complex tables, charts, and scanned images. Compare using standard OCR pipelines versus a Multi-Modal LLM like LLaVA."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The OCR Pipeline (Legacy but precise):** 
   - State that OCR (Tesseract/AWS Textract) + a text-based LLM is highly accurate for raw text, but catastrophically fails at layout analysis. It flattens complex 2D tables into a 1D string, destroying the row/column relationships, making table QA impossible.
2. **The Multi-Modal Approach (The Modern Fix):**
   - Explain that a model like LLaVA processes the PDF as a pure *Image*. It intrinsically understands 2D spatial relationships. It can "look" at a pie chart and tell you which slice is largest, which OCR cannot do.
3. **The Resolution Bottleneck (The Caveat):**
   - Note the fatal flaw of LLaVA: The $336 \times 336$ ViT resolution limit. Dense financial tables will become pixelated and unreadable. 
   - Propose the modern fix (used in models like Qwen-VL or InternVL): **Dynamic High-Resolution Slicing**. Slice a massive 4K document into a grid of 9 smaller $336 \times 336$ images, feed all 9 through the ViT, and concatenate the embeddings before feeding them to the LLM!

---
**Task for the end of the day:** Commit your code to Git. 

You have completed the Advanced Architectures section. You can now build massive MoEs, linear Mambas, and Multi-Modal Vision-Language models. 

Tomorrow, we begin the final, most important enterprise arc of this curriculum: **Retrieval-Augmented Generation (RAG)**! We start with Day 83: Dense Retrieval Foundations.
