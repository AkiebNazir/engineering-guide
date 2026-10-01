# Day 170: Compliance, Governance & AI Ethics

Welcome to Day 170.

This is the final day of the MLOps curriculum. We are ending with the most serious topic in Artificial Intelligence.
If your API crashes, you lose revenue for an hour. If your AI model is found to be racially biased while approving mortgages, your company makes the front page of the New York Times, faces massive class-action lawsuits, and the EU fines you 6% of your global revenue.

Today, we learn **AI Governance**. We will learn about the EU AI Act, PII redacting, and how to mathematically prove that your model is fair and unbiased.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The EU AI Act & Risk Tiers
In 2024, the European Union passed the AI Act. It categorizes AI into four risk tiers:
- **Unacceptable Risk:** (Banned). e.g., AI for social scoring or subliminal manipulation.
- **High Risk:** e.g., AI used in hiring (resume screening), law enforcement, or medical devices. If you build these, you must log every decision, maintain flawless data lineage (Day 165), and submit to government audits.
- **Limited Risk:** e.g., AI Chatbots. You simply must clearly disclose to the user that they are talking to an AI.
- **Minimal Risk:** e.g., AI spam filters. No regulation.

### 2. PII (Personally Identifiable Information)
If an employee asks an internal HR bot, "Summarize the medical leave policy for John Doe, SSN 123-45-678," and that prompt hits the OpenAI API, your company just violated HIPAA and GDPR.
You must implement a **PII Redaction Layer** in your API Gateway. It intercepts the prompt, uses a fast local NLP model (like Microsoft Presidio) to replace the data (`[PERSON_NAME], [SSN]`), sends the redacted prompt to OpenAI, and then re-injects the real data into the response before showing the user.

### 3. Measuring Bias (Fairness Metrics)
Bias in AI usually stems from historically biased training data. If historically, men were approved for loans more often than women, the AI will learn that `Gender=Male` is a positive feature.
Even if you drop the "Gender" column from your dataset, the AI will use **Proxy Variables**. It will realize that people who subscribe to "GQ Magazine" are usually men, and use that to discriminate anyway.
- **Disparate Impact:** A mathematical ratio. If the loan approval rate for women is less than 80% of the approval rate for men, the model is legally considered biased (The "Four-Fifths Rule").
- **Equal Opportunity:** The True Positive Rate must be equal across demographics. (Qualified women should be approved at the exact same rate as qualified men).

### 4. Explainability (XAI)
Deep Neural Networks are "Black Boxes." You cannot look at a matrix of 70 billion floating-point numbers and understand why it denied a loan.
Tools like **SHAP (SHapley Additive exPlanations)** use game theory to calculate exactly how much each feature contributed to a specific prediction. (e.g., "This loan was denied. Income contributed +10% to approval, but Debt contributed -40% to denial.")

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build two crucial Governance components: A PII Redactor for an LLM Gateway, and a Disparate Impact calculator for a Machine Learning model.

*(Note: To run the PII section, you need `pip install presidio-analyzer presidio-anonymizer`)*

### 1. The PII Redaction Gateway
We will simulate an API Gateway that scrubs sensitive data before it ever touches a cloud LLM.

```python
import re

class MockPIIRedactor:
    """
    In production, you would use Microsoft Presidio. 
    We use regex here to simulate the concept.
    """
    def redact(self, prompt: str):
        # Redact Social Security Numbers
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        redacted = re.sub(ssn_pattern, "[REDACTED_SSN]", prompt)
        
        # Redact Phone Numbers
        phone_pattern = r'\b\d{3}-\d{3}-\d{4}\b'
        redacted = re.sub(phone_pattern, "[REDACTED_PHONE]", redacted)
        
        return redacted

def secure_llm_gateway(user_prompt: str):
    redactor = MockPIIRedactor()
    
    print(f"\n[USER INPUT] {user_prompt}")
    
    # 1. Redact before sending to the cloud!
    safe_prompt = redactor.redact(user_prompt)
    print(f"[GATEWAY] Sending to OpenAI: {safe_prompt}")
    
    # 2. Simulate Cloud LLM Processing
    # The LLM never sees the private data!
    response = f"I have processed the request for the user with SSN: [REDACTED_SSN]."
    return response

# Execution
secure_llm_gateway("Please check the background for user with SSN 123-45-6789 and phone 555-123-4567.")
```

### 2. Measuring Disparate Impact (Bias)
Imagine we trained a model to approve or deny credit cards. We must mathematically prove it is fair before deployment.

```python
import pandas as pd

def calculate_disparate_impact(df, protected_attribute, privileged_class, unprivileged_class, prediction_column):
    """
    Calculates the Four-Fifths Rule (Disparate Impact).
    Ratio < 0.8 means the model is biased against the unprivileged class!
    """
    
    # 1. Calculate approval rate for the Privileged class (e.g., Men)
    priv_df = df[df[protected_attribute] == privileged_class]
    priv_approval_rate = priv_df[prediction_column].mean()
    
    # 2. Calculate approval rate for the Unprivileged class (e.g., Women)
    unpriv_df = df[df[protected_attribute] == unprivileged_class]
    unpriv_approval_rate = unpriv_df[prediction_column].mean()
    
    # 3. Calculate the Ratio
    di_ratio = unpriv_approval_rate / priv_approval_rate
    
    print(f"\n--- FAIRNESS AUDIT: {protected_attribute.upper()} ---")
    print(f"Privileged Approval Rate:   {priv_approval_rate:.1%}")
    print(f"Unprivileged Approval Rate: {unpriv_approval_rate:.1%}")
    print(f"Disparate Impact Ratio:     {di_ratio:.2f}")
    
    if di_ratio < 0.80:
        print("🚨 AUDIT FAILED: Model exhibits illegal bias (Ratio < 0.80). DO NOT DEPLOY.")
    else:
        print("✅ AUDIT PASSED: Model falls within acceptable fairness bounds.")

# --- EXECUTION SIMULATION ---
def run_bias_audit():
    # Mock predictions from our Machine Learning model
    data = {
        'gender': ['M', 'M', 'M', 'M', 'M', 'F', 'F', 'F', 'F', 'F'],
        'model_approved_loan': [1, 1, 1, 1, 0, 1, 0, 0, 0, 0] # Men approved 80%, Women 20%
    }
    df = pd.DataFrame(data)
    
    calculate_disparate_impact(
        df=df, 
        protected_attribute='gender', 
        privileged_class='M', 
        unprivileged_class='F', 
        prediction_column='model_approved_loan'
    )

# To run:
# run_bias_audit()
```

### 🔍 Understanding the Enterprise Value
If an ML engineer tries to merge the credit card model into the `main` branch, the CI/CD pipeline (Day 164) will automatically run this `calculate_disparate_impact` script. Because the ratio is `0.25` (which is severely below the legal `0.80` threshold), the CI/CD pipeline will glow red, block the deployment, and save the company from a massive lawsuit!

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
The Disparate Impact calculation is a blunt instrument. Sometimes, the unprivileged class genuinely has lower credit scores in the historical data. 
**Your Task:** Research **Equalized Odds**. It is a stricter fairness metric that ensures the *False Positive Rate* and *True Positive Rate* are equal across demographics, regardless of the underlying baseline rates. 

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your team is building an LLM-powered resume screening tool to automatically filter applicants. As the Lead AI Engineer, design the architecture ensuring it complies with the EU AI Act and standard ethical guidelines."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Risk Categorization:** Acknowledge immediately that this is a "High Risk" system under the EU AI Act because it impacts employment.
2. **Data Lineage & Opt-Out:** Explain that you will use DVC to maintain perfect data lineage. Applicants must be given explicit consent to be evaluated by AI, and must have a button to "Opt-out and request human review."
3. **PII Stripping:** Before the resume hits the LLM, the system must strip Names, Addresses, Graduation Dates (to prevent Ageism), and Club Affiliations (to prevent racial/gender proxy bias).
4. **Continuous Auditing:** Design a Shadow Pipeline where 10% of resumes rejected by the AI are manually reviewed by a human HR rep to calculate the False Negative rate. The CI/CD pipeline must run Disparate Impact audits across gender and race before any model update is deployed.

---
**Task for the end of the day:** Read the executive summary of the **EU AI Act**. It is defining the future of global software engineering.

**🎉 Congratulations!** You have officially completed the MLOps curriculum. You know how to build, scale, monitor, and govern AI at the enterprise level. 

Tomorrow, in **Day 171**, we begin the Grand Finale of this roadmap: **MAANG System Design**. We will combine everything we've learned over 170 days to architect massive AI systems on whiteboards!
