# Day 117: Multi-Modal LLMs (Architecture & Training)

Welcome to Day 117. Up until now, our <abbr title="Artificial Intelligence">AI</abbr> has been completely blind. 
It only understands Text Tokens. If you ask an <abbr title="Large Language Model">LLM</abbr> *"What is in this image?"*, it cannot help you.

But humans don't just read text. We see the world, we watch videos, we hear sounds. 
Today, we bolt "eyes" onto our blind language model. We will learn the architecture of **Large Multi-Modal Models (LMMs)**, specifically focusing on the open-source **LLaVA** architecture.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Multi-Modal Architecture
You cannot feed raw $1024 \times 1024$ pixel values into a Transformer. A Multi-Modal model is actually 3 separate models stitched together:
1. **The Vision Encoder (CLIP):** A pre-trained Vision Transformer (ViT) that looks at an image and generates an array of high-dimensional "Visual Embeddings" (e.g., $256$ vectors representing the concepts in the image).
2. **The Projector:** A tiny neural network layer (an MLP). Think of the Projector as a **Mathematical Translator**. It takes the visual embeddings and translates them into the exact same vector space as the <abbr title="Large Language Model">LLM</abbr>'s text embeddings!
3. **The Language Model:** The <abbr title="Large Language Model">LLM</abbr> receives the translated "Image Tokens", concatenates them with the user's text prompt, and processes them exactly as if they were words!

### 2. LLaVA Training Stage 1: Feature Alignment
How do we train this? 
In Stage 1, we **freeze** the <abbr title="Large Language Model">LLM</abbr> weights and **freeze** the Vision Encoder weights. We ONLY train the tiny Projector!
We feed the system 600,000 Image-Caption pairs. The Projector learns how to translate visual concepts (like a picture of a dog) into the mathematical equivalent of the word "Dog" so the <abbr title="Large Language Model">LLM</abbr> can understand it.

### 3. LLaVA Training Stage 2: Visual Instruction Tuning
In Stage 2, we unfreeze the <abbr title="Large Language Model">LLM</abbr>. 
We train the model on complex conversational datasets about images (e.g., *"Look at this meme and explain why it is funny."*). The <abbr title="Large Language Model">LLM</abbr> learns how to reason about the visual tokens it is receiving.

### 4. Dynamic Resolution
A major problem: If the Vision Encoder only accepts $224 \times 224$ images, how does the model read small text on a massive 4K receipt?
**Dynamic Resolution:** The system splits the 4K image into a grid of 9 smaller "crops". It passes each crop through the Vision Encoder separately, generating hundreds of visual tokens that capture the fine details, and concatenates them all together for the <abbr title="Large Language Model">LLM</abbr>!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's conceptually build the forward pass of a Multi-Modal <abbr title="Large Language Model">LLM</abbr> in PyTorch! We will simulate the Vision Encoder, the Projector translation, and the concatenation of Image and Text!

Create a file named `multimodal_llava.py`:

```python
import torch
import torch.nn as nn

class MockVisionEncoder(nn.Module):
    """Simulates a CLIP Vision Transformer"""
    def forward(self, image_pixels):
        print("[1] Vision Encoder: Analyzing pixels...")
        # Outputs 256 "Visual Concept" vectors, each of size 1024
        return torch.randn(1, 256, 1024) 

class MockTextEmbedding(nn.Module):
    """Simulates standard LLM token embedding"""
    def forward(self, text_tokens):
        print("[1] Text Embedder: Converting words to vectors...")
        # Outputs 10 text vectors, each of size 4096 (The LLM's native dimension)
        return torch.randn(1, 10, 4096)

class ModalityProjector(nn.Module):
    """
    THE TRANSLATOR!
    Takes Vision Embeddings (Size 1024) and projects them to LLM Native Size (4096)
    """
    def __init__(self):
        super().__init__()
        # A simple linear translation matrix!
        self.linear = nn.Linear(1024, 4096)
        
    def forward(self, vision_embeddings):
        print("[2] Projector: Translating Visual concepts into 'Language' tokens...")
        return self.linear(vision_embeddings)

def run_multimodal_forward_pass():
    print("--- RUNNING MULTI-MODAL PIPELINE ---\n")
    
    # 1. Initialize the components
    vision_encoder = MockVisionEncoder()
    text_embedder = MockTextEmbedding()
    projector = ModalityProjector()
    
    # 2. The Inputs
    user_image = torch.randn(1, 3, 224, 224) # A mock RGB image
    user_text = torch.tensor([[101, 453, 992]]) # "What is in this image?"
    
    # 3. Process Modalities Independently
    raw_visual_embeddings = vision_encoder(user_image)
    text_embeddings = text_embedder(user_text)
    
    # 4. TRANSLATE the vision into language!
    translated_image_tokens = projector(raw_visual_embeddings)
    
    print(f"\nShapes before concatenation:")
    print(f"Image Tokens: {translated_image_tokens.shape} (256 visual tokens)")
    print(f"Text Tokens:  {text_embeddings.shape} (10 text tokens)")
    
    # 5. Concatenate! This is the magic. 
    # We smash the image tokens and text tokens together into one massive sequence!
    final_llm_input = torch.cat([translated_image_tokens, text_embeddings], dim=1)
    
    print(f"\n[3] Final Input Sequence to the LLM: {final_llm_input.shape}")
    print("The LLM will now process a sequence of 266 tokens. The first 256 represent the image, the last 10 represent the text prompt!")
    print("The LLM generates text normally from here!")

if __name__ == "__main__":
    run_multimodal_forward_pass()
```

### Key Takeaways from Code:
1. **Everything is a Token:** The <abbr title="Large Language Model">LLM</abbr> does not know what an "Image" is. Thanks to the Projector, the image just looks like 256 normal word embeddings! 
2. **Video Models:** If you want to make this model understand Video, you just extract 1 frame every second, pass them all through the Vision Encoder and Projector, and concatenate thousands of image tokens together!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: OCR vs Native Vision
You have a photo of a restaurant receipt.
**Your Task:**
1. Conceptually map out the old way of doing this: Running a separate Optical Character Recognition (OCR) script (like Tesseract) to extract the text, and passing the text to an <abbr title="Large Language Model">LLM</abbr>.
2. Conceptually map out the new LMM way: Passing the raw photo directly into the LLaVA model.
3. Why is the LMM way better? (Hint: The LMM understands *spatial context*. It knows that the price `$12.99` is physically aligned next to the word `Burger`. OCR destroys spatial context!)

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design an <abbr title="Artificial Intelligence">AI</abbr> system for an insurance company that processes car crash claims automatically. The system receives a raw PDF containing photos of the damaged car, scanned repair shop receipts, and handwritten notes. How do you design the multimodal architecture to output a structured JSON estimate?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Pre-Processing (The PDF Pipeline):** 
   - Extract the images and scanned pages from the PDF.
2. **The Multi-Modal Pipeline (Dynamic Resolution):**
   - Propose using a Vision-Language Model (like GPT-4o or a fine-tuned LLaVA).
   - Emphasize the need for **Dynamic High-Resolution Crops**. The receipts contain tiny text. If you compress the receipt to $224 \times 224$, the text becomes unreadable. You must split the receipt into high-res tiles!
3. **Structured Output:**
   - Propose using **Constrained Decoding** (from Day 112) on the output of the LMM to guarantee the final repair estimate is returned as perfectly valid, database-ready JSON.

---
**Task for the end of the day:** Commit your code to Git. 

We now have intelligent, multi-modal, agentic models.
But frontier models require massive datacenters and internet connectivity. What if you want your <abbr title="Artificial Intelligence">AI</abbr> to run entirely offline on an iPhone to protect user privacy?

Tomorrow, in **Day 118**, we learn **Small Language Models (SLMs) and Mobile Quantization**!
