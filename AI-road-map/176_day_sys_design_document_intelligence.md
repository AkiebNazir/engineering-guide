# Day 176: System Design: Document Intelligence Pipeline

Welcome to Day 176.

For our final System Design deep dive, we tackle a problem that plagues every law firm, hospital, and insurance company on Earth: **Unstructured Documents**.
A hospital receives 10,000 scanned faxes a day. Some are upside down. Some have handwritten doctor's notes. Some contain tables of blood test results. 
If humans process these, it takes weeks. If you just pass them to an <abbr title="Large Language Model">LLM</abbr>, the <abbr title="Large Language Model">LLM</abbr> hallucinates the numbers and someone gets the wrong medication.

Today, we learn how to design a **Document Intelligence Pipeline**. We will learn about OCR, Layout Analysis, and how to use LLMs as deterministic Information Extraction engines.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Multi-Stage Extraction Pipeline
You cannot just feed a PDF to GPT-4. You must build a deterministic pipeline:
1. **Ingestion & Routing:** A webhook receives the PDF. A fast computer vision model classifies it (e.g., "This is a W-2 Tax Form" vs "This is an MRI report").
2. **OCR (Optical Character Recognition):** If it's a scanned image, tools like Tesseract or AWS Textract convert the pixels into raw text.
3. **Layout Analysis:** Raw text is useless if you lose the structure. A model (like LayoutLM) draws bounding boxes around Headers, Paragraphs, and Tables to understand the document's visual hierarchy.
4. **Information Extraction (<abbr title="Large Language Model">LLM</abbr>):** We pass the structured text into an <abbr title="Large Language Model">LLM</abbr> using tools like Instructor/Pydantic (Day 133). We force the <abbr title="Large Language Model">LLM</abbr> to output a strict <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> object (e.g., `{"patient_name": "John", "diagnosis": "Flu"}`).
5. **Human-in-the-Loop (HITL):** If the <abbr title="Large Language Model">LLM</abbr>'s confidence score is < 80%, the document is routed to a human clerk for manual review.

### 2. Layout Analysis vs. OCR
OCR just reads text from left to right.
If you have a two-column newspaper article, OCR will read line 1 of the left column, jump across the gap, and read line 1 of the right column, creating absolute gibberish.
**Layout Analysis** uses Computer Vision to realize there are two separate columns, and instructs the OCR to read the left column top-to-bottom *first*.

### 3. Table Extraction (The Hardest Problem)
Extracting tables from PDFs is notoriously difficult. If a table spans two pages, or has merged cells, simple OCR fails entirely. 
Modern architectures use specific Vision-Language Models (like TableTransformer or specialized multimodal LLMs) that are fine-tuned explicitly to convert an image of a table directly into an HTML `<table>` or Markdown format.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual Python implementation of a Document Intelligence Pipeline. We will simulate receiving a messy PDF, routing it, running OCR, extracting JSON via an LLM, and storing it in a database!

```python
import time
import json
import random

# --- MOCK INFRASTRUCTURE ---

class MockOCR:
    def extract_text(self, document_bytes):
        """Simulates AWS Textract or Tesseract."""
        print("   [OCR] Converting pixels to text & analyzing layout...")
        time.sleep(0.5)
        return "Patient: Jane Doe. Diagnosis: Hypertension. Blood Pressure: 140/90."

class MockLLMExtractor:
    def extract_json(self, raw_text: str):
        """
        Simulates using Instructor/Pydantic to force the LLM 
        to return strict JSON instead of conversational text.
        """
        print("   [LLM] Extracting entities into strict JSON schema...")
        time.sleep(1.0)
        
        # We simulate the LLM also returning a confidence score
        confidence = random.uniform(0.60, 0.99)
        extracted_data = {
            "patient_name": "Jane Doe",
            "diagnosis": "Hypertension",
            "blood_pressure_systolic": 140,
            "blood_pressure_diastolic": 90,
            "extraction_confidence": confidence
        }
        return extracted_data

class PostgresDatabase:
    def insert(self, data: dict):
        print(f"   [DB] Row inserted successfully. Patient: {data['patient_name']}")

# --- THE DOCUMENT PIPELINE ---

def process_medical_document(pdf_file_path: str):
    print(f"\n--- PROCESSING DOCUMENT: {pdf_file_path} ---")
    start_time = time.time()
    
    ocr = MockOCR()
    llm = MockLLMExtractor()
    db = PostgresDatabase()
    
    # 1. OCR & Layout Analysis
    raw_text = ocr.extract_text(pdf_file_path)
    
    # 2. Information Extraction
    json_data = llm.extract_json(raw_text)
    
    # 3. Human-in-the-Loop Routing
    confidence = json_data["extraction_confidence"]
    print(f"   [ROUTER] Extraction Confidence: {confidence:.0%}")
    
    if confidence < 0.85:
        print("   ⚠️ [HITL] Confidence below 85% threshold!")
        print("   Routing document to human medical coder queue...")
        # Do not insert into DB yet!
    else:
        # 4. Storage
        print("   ✅ [AUTOMATION] Confidence high. Bypassing human review.")
        db.insert(json_data)
        
    print(f"Pipeline finished in {(time.time() - start_time):.2f}s")

# --- EXECUTION ---
def run_pipeline():
    # Document 1 (Clean scan, high confidence)
    random.seed(42) # Forces high confidence for demo
    process_medical_document("scans/report_janedoe.pdf")
    
    # Document 2 (Messy handwriting, low confidence)
    random.seed(1) # Forces low confidence for demo
    process_medical_document("scans/handwritten_notes_01.pdf")

# To run:
# run_pipeline()
```

### 🔍 Understanding the Enterprise Value
This architecture saves millions of dollars. If a hospital receives 10,000 documents a day, and this pipeline automates 70% of them (confidence > 85%), the human staff only has to review 3,000 documents. The humans act as a safety net for the <abbr title="Artificial Intelligence">AI</abbr>, while the <abbr title="Artificial Intelligence">AI</abbr> does the heavy lifting.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, our pipeline processes one document at a time synchronously.
**Your Task:** Research **Apache Kafka** or **AWS SQS**. If 10,000 documents are uploaded at exactly 9:00 AM, our synchronous script will crash. Understand how to put the documents into an asynchronous Message Queue, and have a pool of "Worker Nodes" pull documents off the queue at their own pace.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Design a document intelligence platform for a law firm processing 100,000 contracts a day. The system must extract the 'Termination Clause' and the 'Liability Cap'. It must handle PDFs up to 500 pages long."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Asynchronous Architecture:** Draw the S3 bucket triggering an EventBridge event, which drops a message into an SQS queue. A fleet of Kubernetes pods reads the queue to process the PDFs asynchronously (avoiding timeout errors).
2. **Chunking Large Documents:** A 500-page PDF will exceed the <abbr title="Large Language Model">LLM</abbr>'s context window. Propose an architecture where the OCR text is chunked by paragraph, embedded into a Vector Database, and then the system uses **<abbr title="Retrieval-Augmented Generation">RAG</abbr>** to search the document for "termination clause" *before* passing that specific chunk to the <abbr title="Large Language Model">LLM</abbr> for <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> extraction.
3. **The HITL Feedback Loop:** Explain that when a human corrects a low-confidence extraction in the UI, that correction is not just saved to the database. It is logged as "Golden Data" and sent to the <abbr title="Machine Learning">ML</abbr> platform to fine-tune the <abbr title="Large Language Model">LLM</abbr>, ensuring the system gets smarter over time.
4. **Security & PII:** Legal documents are highly confidential. State that the OCR and <abbr title="Large Language Model">LLM</abbr> models must be hosted within the firm's Virtual Private Cloud (VPC), not sent to public OpenAI APIs.

---
**Task for the end of the day:** Review the concept of a **Message Queue** (like RabbitMQ or AWS SQS). It is the backbone of all asynchronous data pipelines.

Tomorrow, in **Day 177**, we transition from Learning to Performing. We will do a deep dive into the **MAANG System Design Interview Framework**. How exactly do you structure a 45-minute whiteboard session to guarantee a "Strong Hire" rating?
