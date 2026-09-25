# Day 71: The Vision Transformer (ViT) & Multi-Modal AI

Welcome to Day 71. For an entire decade, Convolutional Neural Networks (CNNs like ResNet) were the undisputed kings of Computer Vision. 

But in 2020, researchers at Google asked a crazy question: *What if we just threw the <abbr title="Convolutional Neural Network">CNN</abbr> in the garbage, treated an image exactly like a sentence of words, and fed it into a Transformer Encoder?*

The result was the **Vision Transformer (ViT)**. It destroyed the state-of-the-art and unified the fields of <abbr title="Natural Language Processing">NLP</abbr> and Vision forever.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Image as a Sentence
A standard image is $224 \times 224$ pixels. That is $50,176$ pixels.
Because Attention scales quadratically $O(N^2)$, you physically cannot feed $50,176$ tokens into a Transformer. It would require terabytes of VRAM.
**The Fix:** ViT slices the image into a $14 \times 14$ grid. Each square in the grid is a $16 \times 16$ pixel "Patch". 
$14 \times 14 = 196$ total patches.

### 2. The Patch Embedding
To the Transformer, each of these 196 patches is a "word". 
We flatten the pixels in a patch ($16 \times 16 \times 3 \text{ RGB channels} = 768$ numbers). 
We pass this flat 768-dimensional array through a single `nn.Linear` layer to embed it. 
It is now mathematically indistinguishable from a word embedding!

### 3. The ViT Architecture
Once we have the 196 embeddings, we do exactly what we did with BERT on Day 65!
1. We prepend a `[CLS]` token at index 0. (Now we have 197 tokens).
2. We add Positional Encodings so the Transformer knows if a patch came from the top-left or bottom-right of the image.
3. We pass all 197 tokens through 12 layers of a standard Transformer Encoder.
4. We throw away the 196 patch tokens, grab the `[CLS]` token, and pass it through a classifier to predict if the image is a Dog or a Cat!

### 4. The Inductive Bias Flaw
Why didn't we do this earlier? Because of **Inductive Bias**.
CNNs have a strong inductive bias: The math of a convolutional filter inherently assumes that pixels physically next to each other are related. 
ViT has **NO** inductive bias. It doesn't know that Patch 1 and Patch 2 are next to each other. It has to figure it out from scratch. 
Because of this, if you train ViT on a small dataset (like 50,000 images), it fails completely. But if you train it on 300 Million images, its lack of assumptions allows it to learn deeper, more complex relationships than a <abbr title="Convolutional Neural Network">CNN</abbr> ever could!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the core innovation of ViT: The Patch Embedding Layer.
We won't use a slow `for` loop to slice the image. We will use a brilliant mathematical trick using `nn.Conv2d` to extract all the patches in parallel!

Create a file named `vision_transformer.py`:

```python
import torch
import torch.nn as nn

class PatchEmbedding(nn.Module):
    """
    Turns a 2D Image into a 1D sequence of "Words"!
    """
    def __init__(self, in_channels=3, patch_size=16, embed_dim=768):
        super().__init__()
        self.patch_size = patch_size
        
        # THE MAGIC TRICK:
        # We use a 2D Convolution with a kernel size AND stride equal to the patch size!
        # This perfectly slices the image into non-overlapping grids and projects 
        # the pixels into our 768-dimensional embedding space simultaneously!
        self.proj = nn.Conv2d(
            in_channels, 
            embed_dim, 
            kernel_size=patch_size, 
            stride=patch_size
        )

    def forward(self, x):
        # Input shape: [Batch, Channels, Height, Width]
        # Example: [1, 3, 224, 224]
        
        # 1. Slice and Project
        # Shape: [Batch, Embed_Dim, Grid_H, Grid_W] -> [1, 768, 14, 14]
        x = self.proj(x)
        
        # 2. Flatten the spatial dimensions (The 14x14 grid becomes 196 "Words")
        # Shape: [Batch, Embed_Dim, Num_Patches] -> [1, 768, 196]
        x = x.flatten(2)
        
        # 3. Transpose to match standard Transformer sequence format!
        # Final Shape: [Batch, Seq_Len, Embed_Dim] -> [1, 196, 768]
        x = x.transpose(1, 2)
        
        return x

def test_vit_embeddings():
    print("--- RUNNING ViT PATCH EMBEDDING ---")
    
    BATCH_SIZE = 1
    CHANNELS = 3
    IMAGE_SIZE = 224 # Standard ImageNet size
    PATCH_SIZE = 16
    EMBED_DIM = 768  # Standard BERT base dimension
    
    # Simulate a blank RGB image
    image = torch.randn(BATCH_SIZE, CHANNELS, IMAGE_SIZE, IMAGE_SIZE)
    
    embedder = PatchEmbedding(in_channels=CHANNELS, patch_size=PATCH_SIZE, embed_dim=EMBED_DIM)
    
    sequence = embedder(image)
    
    print(f"Original Image: {image.shape}")
    print(f"ViT Sequence:   {sequence.shape}")
    
    num_patches = (IMAGE_SIZE // PATCH_SIZE) ** 2
    print(f"\nMath Check: ({IMAGE_SIZE} / {PATCH_SIZE})^2 = {num_patches} patches.")
    print("The image is now just a sentence of 196 words. You can feed this directly into BERT!")

if __name__ == "__main__":
    test_vit_embeddings()
```

### Key Takeaways from Code:
1. **The `Conv2d` Hack:** Instead of writing complex array-slicing code, we use `kernel_size=16, stride=16`. The Convolution literally jumps 16 pixels at a time, looking at exactly one patch per jump, and mathematically projecting the RGB values into 768 dimensions!
2. **The Final Shape:** The output is `[Batch, 196, 768]`. This is the *exact same shape* as a 196-word sentence passing through BERT!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Multi-Modal Search Engine
ViT is the backbone of CLIP (Day 60). 
**Your Task:**
1. Imagine you have a database of 1 Million product images. 
2. Mentally design a script that passes all 1M images through CLIP's ViT Encoder, yielding 1M embeddings of size 512.
3. Save these embeddings to a Vector Database using `FAISS` (Facebook <abbr title="Artificial Intelligence">AI</abbr> Similarity Search).
4. When a user types *"Red running shoes"*, pass that text through CLIP's Text Encoder.
5. Do a simple dot-product similarity search between the text embedding and the 1M image embeddings in FAISS to instantly retrieve the visual products!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a visual search system for an e-commerce platform with 100M products. Discuss embedding generation, indexing strategies like FAISS/ScaNN, and the overall serving architecture."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Embedding Generation (Offline):** 
   - State that running 100M images through a ViT/CLIP model live is impossible. Embeddings must be generated offline in a batch data pipeline (Spark/Airflow) using heavy GPU clusters and saved to a database.
2. **Indexing (The FAISS bottleneck):**
   - Explain that calculating exact Cosine Similarity for 100M vectors takes seconds. You MUST use **ANN (Approximate Nearest Neighbors)**. 
   - Propose using FAISS with **IVF-<abbr title="Priority Queue. An abstract data type similar to a regular queue or stack in which each element additionally has a priority associated with it.">PQ</abbr> (Inverted File Index with Product Quantization)**. IVF clusters the vectors into Voronoi cells so you only search a fraction of the DB. <abbr title="Priority Queue. An abstract data type similar to a regular queue or stack in which each element additionally has a priority associated with it.">PQ</abbr> mathematically compresses the 512D floats into 8-bit integers, drastically reducing <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> usage.
3. **Serving Architecture (Live):**
   - Detail the live workflow: User uploads an image $\rightarrow$ <abbr title="Application Programming Interface">API</abbr> Gateway $\rightarrow$ GPU Inference Service (generates 1 ViT embedding) $\rightarrow$ FAISS index (retrieves Top 100 IDs) $\rightarrow$ Metadata DB (Postgres/Redis) to fetch product prices and URLs $\rightarrow$ Return to user.

---
**Task for the end of the day:** Commit your code to Git. You have united Vision and <abbr title="Natural Language Processing">NLP</abbr>!

Tomorrow, in **Day 72**, we tackle the biggest hardware bottleneck in Deep Learning. We will learn how **Flash Attention** tricks the GPU memory hierarchy to make Transformers run 3x faster!
