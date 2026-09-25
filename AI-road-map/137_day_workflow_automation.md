# Day 137: Workflow Automation (Enterprise Integration)

Welcome to Day 137. 

Most <abbr title="Artificial Intelligence">AI</abbr> tutorials end with a script running in your terminal. But in the real world, enterprise businesses do not run in terminals. They run on event-driven workflows, CRMs (Salesforce), ticketing systems (Jira), and messaging apps (Slack).

Today, we take our Agents out of the sandbox and wire them into **Enterprise Event-Driven Architectures**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Event-Triggered vs Agent-Triggered
There are two ways an Agent interacts with a workflow:
- **Event-Triggered (Reactive):** The Agent is asleep. A customer submits a Zendesk ticket. Zendesk fires a Webhook to your AWS <abbr title="Application Programming Interface">API</abbr> Gateway. This instantly wakes up the Agent, passing the ticket data directly into its prompt.
- **Agent-Triggered (Proactive):** The Agent is awake and analyzing data. It realizes the data is stale. The Agent makes an <abbr title="Application Programming Interface">API</abbr> call to Airflow, triggering a massive Spark ETL pipeline, and then goes to sleep until Airflow pings it back!

### 2. The Integration Layer (Webhooks & Message Queues)
Agents are slow. If a webhook expects a response in 3 seconds, but your Agent takes 30 seconds to think, the webhook will timeout and crash. 
To fix this, you must use **Message Queues (AWS SQS, Kafka, RabbitMQ)**. 
The Webhook drops the payload into the Queue and instantly returns a `200 OK`. A worker pool of Agents pulls payloads from the Queue at their own pace.

### 3. Workflow Engines
Instead of writing complex <abbr title="Application Programming Interface">API</abbr> routing in Python, enterprises use workflow engines like **Temporal, n8n, or Zapier**. These platforms handle the <abbr title="Application Programming Interface">API</abbr> authentication, retry logic, and timeouts. You simply add an "<abbr title="Artificial Intelligence">AI</abbr> Agent Node" in the middle of their visual drag-and-drop graph!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build an **Event-Triggered Customer Support Workflow**. We will simulate a Webhook hitting our server, our Agent processing it, querying a CRM, and generating an automated resolution.

Create a file named `workflow_automation.py`:

```python
import json
import time

# --- 1. MOCK ENTERPRISE SYSTEMS ---
class MockCRM:
    def get_customer(self, email):
        print(f"   [CRM API] Fetching data for {email}...")
        if email == "vip@client.com":
            return {"tier": "Enterprise", "monthly_spend": 5000, "status": "Active"}
        return {"tier": "Free", "monthly_spend": 0, "status": "Active"}

class MockZendesk:
    def resolve_ticket(self, ticket_id, response_text):
        print(f"   [ZENDESK API] Ticket {ticket_id} closed with message: '{response_text}'")

# --- 2. THE WORKFLOW AGENT ---
def support_agent_workflow(webhook_payload):
    """
    This function is triggered automatically when a Webhook hits our server.
    """
    print("\n--- NEW EVENT TRIGGERED ---")
    data = json.loads(webhook_payload)
    print(f"[SYSTEM] Received Ticket #{data['ticket_id']} from {data['email']}")
    print(f"[SYSTEM] Message: '{data['message']}'")
    
    # 1. Agent extracts intent and entities (Simulated LLM Call)
    print("\n[AGENT] Analyzing intent...")
    intent = "password_reset" if "password" in data['message'] else "unknown"
    
    # 2. Agent queries the CRM Tool
    crm = MockCRM()
    customer_data = crm.get_customer(data['email'])
    
    # 3. Agent formulates a plan based on enterprise rules
    print(f"\n[AGENT] Customer is {customer_data['tier']} tier. Intent is {intent}.")
    
    if customer_data["tier"] == "Enterprise":
        print("[AGENT] Enterprise customers get white-glove service. Generating polite response...")
        response = "Dear VIP, we have initiated a manual password reset. Our concierge will call you."
    else:
        print("[AGENT] Free tier customer. Sending automated documentation link...")
        response = "Please follow the instructions at docs.company.com/reset to reset your password."
        
    # 4. Agent executes the final action
    zendesk = MockZendesk()
    zendesk.resolve_ticket(data["ticket_id"], response)

# --- 3. THE EVENT SIMULATOR ---
def run_event_simulation():
    print("--- STARTING WEBHOOK LISTENER ---")
    
    # Simulating an incoming webhook payload from a free user
    payload_1 = json.dumps({
        "ticket_id": "1001",
        "email": "user@gmail.com",
        "message": "I forgot my password."
    })
    
    # Simulating an incoming webhook payload from an enterprise VIP
    payload_2 = json.dumps({
        "ticket_id": "1002",
        "email": "vip@client.com",
        "message": "URGENT: Password reset not working for my team."
    })
    
    # The workflow executes asynchronously as events arrive
    support_agent_workflow(payload_1)
    time.sleep(1)
    support_agent_workflow(payload_2)

if __name__ == "__main__":
    run_event_simulation()
```

### Key Takeaways from Code:
1. **No Infinite Loops:** Notice that this is not a ReAct `while` loop. In highly deterministic enterprise workflows, you don't want the agent guessing what to do. You define the rigid <abbr title="Application Programming Interface">API</abbr> steps (Extract -> Query CRM -> Resolve) and only use the <abbr title="Large Language Model">LLM</abbr> for the "thinking" parts (Intent Extraction and Text Generation).
2. **Context-Aware Decisions:** The Agent's output drastically changed depending on the CRM <abbr title="Application Programming Interface">API</abbr> response. This proves the Agent is deeply integrated into the business logic.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Automated Recruiter
You are automating a hiring pipeline.
**Your Task:**
1. Conceptually design an Agent-Triggered workflow.
2. The Webhook: A candidate submits a Resume PDF.
3. Node 1: Agent extracts skills from PDF.
4. Node 2: Agent queries the HR Database (Greenhouse <abbr title="Application Programming Interface">API</abbr>) to match skills against open Job Reqs.
5. Node 3: If match score > 80%, the Agent triggers a Calendly <abbr title="Application Programming Interface">API</abbr> to email the candidate an interview link.
6. Write out the architecture. What happens if the Calendly <abbr title="Application Programming Interface">API</abbr> is down? Where does the message go? (Hint: Dead Letter Queue).

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design an <abbr title="Artificial Intelligence">AI</abbr>-powered operations platform that automates 80% of IT support tickets. Cover: ticket classification, automated resolution, escalation, and human handoff."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Ingestion & Queuing Layer:** 
   - State that all incoming tickets must hit an SQS Queue. A fast <abbr title="Large Language Model">LLM</abbr> (Classifier) pulls from the queue and routes the ticket to the correct specialized Agent (Network Agent, Hardware Agent, Password Agent).
2. **The Execution Layer:**
   - The Specialized Agent attempts to resolve the issue using its specific Tools (e.g., pinging a router, resetting Active Directory).
3. **Escalation & Handoff:**
   - If the Agent encounters an error, or if the user responds with *"This didn't fix it!"*, the Agent must instantly halt.
   - It summarizes the entire debugging trajectory and attaches it as an internal note to the ticket, routing it to a Human IT Queue so the human doesn't have to start from scratch.

---
**Task for the end of the day:** Commit your code to Git. 

We have fully automated our enterprise workflow. But there is a massive danger. What if our Agent hallucinates and decides to delete the CEO's Active Directory account?

Tomorrow, in **Day 138**, we learn the ultimate safety protocol for production <abbr title="Artificial Intelligence">AI</abbr>: **Human-in-the-Loop (HITL) and Approval Gates**!
