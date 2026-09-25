# 27. LLM Safety & Guardrails (Guardrails AI, NeMo)

Welcome to LLM Safety. You've evaluated your model, and it scores a 98% on the Golden Dataset. You deploy it. 
An hour later, a hacker uses a "jailbreak" prompt to convince your customer service bot to sell a $50,000 car for $1. Or, a user asks it for instructions on how to build a bomb, and it happily complies.

Evaluation happens *before* deployment. **Guardrails** happen *during* deployment, in real-time, right before the text reaches the user.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Firewall Analogy
Think of Guardrails like a Web Application Firewall (WAF) for LLMs. 
- **Input Guardrails:** Scan the user's prompt *before* it hits the LLM. If it contains a known jailbreak (like "Ignore all previous instructions..."), block it immediately.
- **Output Guardrails:** Scan the LLM's response *before* sending it to the user. If the LLM generates PII (Social Security Numbers), toxic language, or hallucinated competitor mentions, redact or block it.

### 2. NeMo Guardrails (NVIDIA)
NeMo Guardrails uses a domain-specific language called Colang. It is highly stateful and designed for conversational bots. You can define "flows". If the user asks about politics, NeMo instantly routes the conversation away: *"I am a banking assistant, I cannot discuss politics."*

### 3. Guardrails AI (Schema Enforcement)
Guardrails AI focuses heavily on structure and validation. If you ask an LLM to output a JSON object containing a user's age, Guardrails AI will sit on top of the LLM. If the LLM outputs `{"age": 150}`, Guardrails AI will validate it against a rule (`age < 120`), catch the error, and automatically re-prompt the LLM to fix its mistake under the hood!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a mock script using `Guardrails AI` to enforce that an LLM never mentions a competitor's name in its output.

Create a file named `competitor_guardrail.py`:

```python
# Note: Conceptual code demonstrating the Guardrails AI SDK.
# pip install guardrails-ai
import guardrails as gd
from guardrails.validators import CompetitorCheck

def run_guardrail():
    print("--- STARTING GUARDRAILS PROXY ---")
    
    # 1. Define the Rules (The Guard)
    # We want to ensure the LLM never mentions 'Apple' or 'Samsung'
    # because we are building a chatbot for a fictional phone company.
    guard = gd.Guard().with_prompt_validation(
        validators=[CompetitorCheck(competitors=["Apple", "Samsung"])]
    )
    
    # 2. The LLM Output (Simulated)
    # Imagine the user asked: "What is the best phone?"
    # The LLM generates a response that violates our business rules!
    unsafe_llm_output = "While our phone is great, the Apple iPhone has a better camera."
    print(f"Raw LLM Output: {unsafe_llm_output}")
    
    # 3. Intercept and Validate!
    try:
        print("\nRunning Output Guardrail...")
        # In a real app, you pass the LLM callable to the guard, and it handles generation.
        validated_output = guard.parse(unsafe_llm_output)
        print(f"Validated Output: {validated_output}")
    except Exception as e:
        # 4. Action on Failure
        # If the output violates the rule, Guardrails throws an exception,
        # preventing the dangerous text from ever reaching the user!
        print("🚨 GUARDRAIL TRIGGERED: Policy Violation!")
        print(f"Error: {e}")
        
        # Fallback response
        print("\nSending safe fallback to user:")
        print("User-Facing Output: 'I can only provide information about our proprietary devices.'")

if __name__ == "__main__":
    run_guardrail()
```

### Key Takeaways from Code:
1. **The Proxy Layer:** The guardrail acts as an API proxy. Your frontend never talks directly to the LLM; it talks to the Guardrail.
2. **Deterministic Safety:** Neural networks are unpredictable. Guardrails add deterministic, hard-coded safety logic (Regex, API lookups) back into the unpredictable AI loop.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: PII Redaction
You are processing medical records.
**Your Task:**
1. Research how to implement an **Input Guardrail** for PII (Personally Identifiable Information).
2. Use Microsoft Presidio (a common tool integrated into Guardrails) to intercept a prompt: *"Can you summarize John Doe's medical history? His SSN is 123-45-6789."*
3. The guardrail should redact the input so the LLM actually receives: *"Can you summarize [PERSON]'s medical history? His SSN is [REDACTED]."* This prevents PII from leaking to OpenAI's servers!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Guardrails add significant latency to real-time chat applications because you have to run secondary classifiers and regex engines on every token. How would you architect a safety system that minimizes latency while maintaining strict safety compliance?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:
1. **Streaming Validation:** Propose running output guardrails on chunks of tokens asynchronously as they stream, rather than waiting for the entire LLM generation to finish. 
2. **Tiered Guardrails:** Run cheap, fast guardrails (Regex, Keyword blacklists) directly in the critical path. Run expensive, slow guardrails (LLM-as-a-Judge toxicity checks) asynchronously.
3. **Semantic Routing:** Cache safe responses. If the user asks a mathematically identical question to a previously vetted query, return the cached safe response instantly, bypassing the LLM and the expensive guardrails entirely.
