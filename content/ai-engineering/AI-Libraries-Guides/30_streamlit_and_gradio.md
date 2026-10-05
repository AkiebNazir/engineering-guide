# Streamlit & Gradio Mastery: Turning a Model into a Demo App

## 1. The Core Concept (What and Why)

*Why is this tool relevant?* By now you can train a classifier (Guide 03), fine-tune an LLM (Guides 09-10), build a RAG chain or an agent (Guides 11-15) and serve a model (Guides 20-21). But a Python function in a notebook can't be shown to a product manager, tested by a domain expert, or shared with a user research session. Building a React frontend plus an API for a two-week experiment is overkill. **Streamlit** and **Gradio** let you put a web UI on a Python function in tens of lines, with no HTML, CSS or JavaScript.

**What are they?**
- **Streamlit** is a framework for data apps and dashboards. You write a normal top-to-bottom Python script that calls `st.title`, `st.slider`, `st.dataframe`, `st.chat_message`...; Streamlit turns each call into a widget. When the user touches any widget, **the whole script re-runs** from the top with the new widget values.
- **Gradio** (owned by Hugging Face) is a framework for **ML demos**: you declare input components, output components and the Python function that connects them. Only that function runs when an event fires. Every Gradio app also exposes an HTTP API and a Python/JS client for free, and it's the default way to build a Hugging Face Space.

**Why do they exist?**
Data scientists write Python; web apps need a server, routing, state, and a frontend. Both libraries hide the web layer: they run a server (Tornado for Streamlit, FastAPI for Gradio), render a prebuilt frontend, and sync widget state over a WebSocket or HTTP/SSE.

**Which one?**

| | Streamlit | Gradio |
| --- | --- | --- |
| Mental model | A script that re-runs top to bottom on every interaction | Components + event listeners (`btn.click(fn, inputs, outputs)`) |
| Best at | Dashboards, data exploration, multi-page internal tools, charts | Model demos: image/audio/video/chat I/O, Hugging Face Spaces |
| Free API | No (it's a UI) | Yes: every event is an endpoint, plus `gradio_client` and an optional MCP server |
| Concurrency control | You add it (caching, your own limits) | Built-in request queue with per-event concurrency limits |
| State | `st.session_state` (per browser tab) | `gr.State` (per session) / component values |
| Hosting | Streamlit Community Cloud, Snowflake, any container | Hugging Face Spaces, any container, mountable inside FastAPI |

Rule of thumb: **a dashboard over data → Streamlit; a demo of a model's inputs and outputs → Gradio.** For chat UIs both are fine.

---

## 2. Setup & Installation

```bash
pip install streamlit gradio
```

```python
import gradio as gr
import streamlit as st

print(f"Streamlit: {st.__version__}")   # 1.5x+ in 2026
print(f"Gradio: {gr.__version__}")      # 6.x in 2026 (5.x API is very close; differences noted below)
```

Run a Streamlit app with `streamlit run app.py` (opens `http://localhost:8501`). Run a Gradio app with `python app.py` (serves `http://127.0.0.1:7860`), or `gradio app.py` for auto-reload while developing.

---

## 3. The "Hello World": One Function, Two Frameworks

### Gradio: `gr.Interface`

```python
import gradio as gr


def greet(name: str, intensity: int) -> str:
    return "Hello, " + name + "!" * intensity


demo = gr.Interface(
    fn=greet,
    inputs=[gr.Textbox(label="Name"), gr.Slider(1, 10, value=2, step=1, label="Intensity")],
    outputs=gr.Textbox(label="Greeting"),
    title="Greeter",
)

if __name__ == "__main__":
    demo.launch()          # share=True gives a temporary public *.gradio.live URL
```

`gr.Interface` maps the function's arguments to input components and its return value(s) to output components. That's the whole API for simple demos.

### Streamlit: a script

```python
# app.py  ->  streamlit run app.py
import streamlit as st

st.title("Greeter")
name = st.text_input("Name", "world")
intensity = st.slider("Intensity", 1, 10, 2)
st.write("Hello, " + name + "!" * intensity)
```

No callback: when the slider moves, Streamlit re-runs `app.py` from the top, `st.slider` returns the new value, and the page re-renders. This is simple to reason about and is the source of most Streamlit performance bugs (Section 4).

---

## 4. Deep Dive: Streamlit's Execution Model

### Reruns, caching and state

Because the script re-runs on every click, anything expensive in it (loading a model, reading a 2 GB CSV, calling an API) would repeat on every click. Two decorators fix that, and a dictionary keeps state across reruns:

| Tool | Stores | Shared across users? | Use for |
| --- | --- | --- | --- |
| `@st.cache_resource` | The object itself (not copied) | Yes, one per server process | Models, DB connections, LLM clients: things that are expensive to create and safe to share |
| `@st.cache_data` | A pickled copy of the return value, keyed by the arguments | Yes, but each caller gets a copy | DataFrames, API responses, computed results (supports `ttl=`) |
| `st.session_state` | Arbitrary values | No, one per browser tab | Chat history, the current step of a wizard, user choices |

### A streaming chat app (runs offline with a stand-in model)

```python
# chat_app.py  ->  streamlit run chat_app.py
import time

import streamlit as st

st.set_page_config(page_title="Support Bot", page_icon=":speech_balloon:")
st.title("Support Bot")


@st.cache_resource            # runs once per server process, shared by all sessions
def load_model():
    time.sleep(0.1)           # stand-in for loading an LLM client / weights
    return lambda prompt, temperature: f"(t={temperature}) You asked about: {prompt}"


def stream_words(text):
    for word in text.split():
        yield word + " "
        time.sleep(0.02)


model = load_model()

with st.sidebar:
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    if st.button("Clear chat"):
        st.session_state.messages = []

if "messages" not in st.session_state:         # per-browser-session state survives reruns
    st.session_state.messages = []

for msg in st.session_state.messages:          # redraw history on every rerun
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about orders, shipping, returns..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        reply = st.write_stream(stream_words(model(prompt, temperature)))   # returns the full text
    st.session_state.messages.append({"role": "assistant", "content": reply})
```

To use a real LLM, replace `load_model` with a cached client (for example an OpenAI-compatible client pointed at vLLM, Guide 20) and pass its streaming iterator to `st.write_stream`, which accepts generators and OpenAI-style stream objects.

### Testing a Streamlit app without a browser (runs offline)

`streamlit.testing.v1.AppTest` runs the script headlessly and lets you set widget values, so UI logic goes into your normal pytest suite:

```python
# test_chat_app.py  ->  pytest test_chat_app.py   (next to chat_app.py)
from streamlit.testing.v1 import AppTest


def test_chat_round_trip():
    at = AppTest.from_file("chat_app.py", default_timeout=10).run()
    assert at.title[0].value == "Support Bot"
    assert not at.exception

    at.sidebar.slider[0].set_value(0.2)
    at.chat_input[0].set_value("Where is my order?").run()

    messages = at.session_state.messages
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert "(t=0.2)" in messages[1]["content"]
    assert len(at.chat_message) == 2


def test_clear_button():
    at = AppTest.from_file("chat_app.py").run()
    at.chat_input[0].set_value("hi").run()
    at.sidebar.button[0].click().run()
    assert at.session_state.messages == []
```

### Other Streamlit tools you'll use
- `st.form("name")`: batch several inputs so the script re-runs once on submit, not on every keystroke.
- `@st.fragment`: re-run only one function's part of the page (e.g. a live-updating chart) instead of the whole script.
- Layout: `st.columns`, `st.tabs`, `st.sidebar`, `st.expander`; multi-page apps via `st.navigation` / a `pages/` folder.
- Data: `st.dataframe`, `st.data_editor`, `st.line_chart`, `st.pyplot(fig)` (Guide 26), `st.plotly_chart`.
- Auth: `st.login()` / `st.user` for OpenID Connect sign-in (configured in `secrets.toml`); secrets via `st.secrets`.

---

## 5. Deep Dive: Gradio Blocks, Events and the Free API

`gr.Interface` is one function. For anything else use **`gr.Blocks`**: you place components in rows, columns and tabs, then wire events explicitly.

```python
import time

import gradio as gr


def classify(text: str, threshold: float) -> tuple[dict, str]:
    """Stand-in for a model: 'sentiment' from a tiny word list."""
    words = text.lower().split()
    pos = sum(w in {"love", "great", "good", "fast"} for w in words)
    neg = sum(w in {"hate", "bad", "slow", "broken"} for w in words)
    p = (pos + 1) / (pos + neg + 2)                      # Laplace-smoothed "probability"
    verdict = "POSITIVE" if p >= threshold else "NEGATIVE"
    return {"positive": p, "negative": 1 - p}, verdict


def respond(message: str, history: list[dict]):
    """ChatInterface handler: history is a list of {'role', 'content'} dicts. Yield to stream."""
    reply = f"You said '{message}'. This is turn {len(history) // 2 + 1}."
    partial = ""
    for word in reply.split():
        partial += word + " "
        time.sleep(0.01)
        yield partial.strip()                           # yield the text so far, not the delta


with gr.Blocks(title="Model demo") as demo:
    gr.Markdown("# Model demo")
    with gr.Tab("Classifier"):
        with gr.Row():
            with gr.Column():
                text = gr.Textbox(label="Review", lines=3, placeholder="Type a product review")
                threshold = gr.Slider(0, 1, value=0.5, step=0.05, label="Decision threshold")
                btn = gr.Button("Classify", variant="primary")
            with gr.Column():
                probs = gr.Label(label="Scores")
                verdict = gr.Textbox(label="Verdict")
        btn.click(classify, inputs=[text, threshold], outputs=[probs, verdict], api_name="classify")
        gr.Examples([["I love it, great and fast", 0.5], ["slow and broken", 0.5]], inputs=[text, threshold])
    with gr.Tab("Chat"):
        gr.ChatInterface(respond, api_name="chat")

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=4)   # at most 4 concurrent runs per event (protects the GPU)
    demo.launch(server_name="127.0.0.1", server_port=7860)
```

### Parameter Breakdown: events and the queue
- `btn.click(fn, inputs=[...], outputs=[...])`: when clicked, Gradio reads the input components' values, calls `fn` with them in order, and writes the returned values into the outputs in order. Other events: `.change`, `.submit`, `.upload`, `.select`; chain with `.then(...)`.
- **Generators stream**: if `fn` yields, each yield updates the outputs. For chat, yield the *accumulated* text.
- `api_name="classify"`: names the HTTP endpoint for this event (use `api_visibility="private"` to hide one in Gradio 6; in 5.x the equivalent was `show_api=False`/`api_name=False`).
- **The queue**: every event goes through a server-side queue. `default_concurrency_limit` (default 1) is how many requests for the same event run at once; the rest wait and see their queue position. Set it per event with `concurrency_limit=`. One GPU model usually means a limit of 1 to a few; raising it just causes out-of-memory errors (Guide 08).
- `gr.State()`: a per-session value passed in and out of functions like a component.
- *Gradio 6 note:* chat history is always a list of `{"role", "content"}` messages (5.x needed `type="messages"` on `Chatbot`/`ChatInterface`), and app-level `theme=`/`css=` moved from `gr.Blocks(...)` to `launch(...)`.

### Calling a Gradio app as an API (runs offline, against a local server)

Every named event is an endpoint. `gradio_client` calls it from Python (there is a JS client too), which makes Gradio apps easy to test and to chain.

```python
# client_test.py  (next to the Blocks app above, saved as gr_app.py)
from gradio_client import Client

from gr_app import demo

demo.queue(default_concurrency_limit=4)
_, url, _ = demo.launch(server_name="127.0.0.1", server_port=7861, prevent_thread_lock=True, quiet=True)

client = Client(url, verbose=False)
print(client.view_api(print_info=False, return_format="dict")["named_endpoints"].keys())
# dict_keys(['/classify', '/chat'])
print(client.predict("I love it, great and fast", 0.5, api_name="/classify"))
# ({'label': 'positive', 'confidences': [{'label': 'positive', 'confidence': 0.8}, ...]}, 'POSITIVE')
print(client.predict("hello", api_name="/chat"))
# You said 'hello'. This is turn 1.
demo.close()
```

The same client works against a public Space: `Client("some-user/some-space")` (network). And with `pip install "gradio[mcp]"`, `demo.launch(mcp_server=True)` also exposes each endpoint as an MCP tool, so an agent (Guide 16) can call your demo.

---

## 6. Pro Level: Wrapping a Real Model (downloads a model)

A realistic pattern: load the model **once at import time** (not inside the handler), keep the handler thin, and let the queue protect the hardware.

```python
import gradio as gr
from transformers import pipeline

classifier = pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")


def predict(text: str) -> dict:
    result = classifier(text, top_k=None)            # all labels with scores
    return {r["label"]: r["score"] for r in result}


demo = gr.Interface(predict, gr.Textbox(lines=3), gr.Label(num_top_classes=2), title="Sentiment")

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=2).launch()
```

**Batching for GPUs.** `btn.click(fn, ..., batch=True, max_batch_size=16)` makes Gradio collect up to 16 queued requests and call `fn` once with lists of inputs, which uses the GPU far better than 16 separate calls. Your function must then accept and return lists.

**Deploying.**
- *Hugging Face Spaces*: push `app.py` + `requirements.txt` to a Space repo (Gradio or Streamlit SDK, or Docker). Free CPU tiers sleep when idle; GPUs and ZeroGPU (shared GPUs allocated per call via the `@spaces.GPU` decorator) are available.
- *Streamlit Community Cloud*: connect a GitHub repo; the app redeploys on push.
- *Your own infrastructure*: a container behind a reverse proxy. Streamlit needs WebSocket support and sticky sessions if you run several replicas (state lives in the server process). Gradio can be mounted inside an existing FastAPI app with `gr.mount_gradio_app(app, demo, path="/demo")`.

---

## 7. Production: Where Demos End

These tools are for demos, internal tools and prototypes. Before real users arrive, know the limits:

1. **Authentication and authorization.** `demo.launch(auth=...)` is a basic password gate; `st.login` gives SSO. Anything beyond that (roles, per-user data isolation, audit logs) belongs in a real app or behind an authenticating proxy.
2. **Scaling.** Streamlit keeps each session's state in server memory and re-runs the script per interaction, so CPU and memory grow with concurrent users. Gradio's queue protects a model but one process still serves everyone. For real traffic, serve the model separately (vLLM, TGI, Triton, Guides 20-21) and make the UI a thin client of that service.
3. **Public share links are public.** `share=True` exposes your laptop's app to anyone with the URL, including every endpoint in its API. Never share an app that has file-system access, secrets or a paid API key without auth.
4. **Secrets.** Use `st.secrets`, environment variables or the Space's secret settings; never hard-code API keys in `app.py`, which is often pushed to a public Space.
5. **Observability.** Log inputs/outputs (with consent) and latency; demo feedback is valuable evaluation data (Guide 27). Gradio's `flagging` and the chatbot's like/dislike buttons collect it with no extra code.
6. **Upgrade carefully.** Both libraries release often; pin versions in `requirements.txt`, especially for Spaces that rebuild on restart.

---

## 8. MAANG Interview Scenarios

### Scenario 1: The Slow Streamlit App
*Interviewer:* "A Streamlit app that summarises documents takes 20 seconds every time a user changes a dropdown, even if the dropdown is unrelated to the summary. Why, and how do you fix it?"

*Answer:* "Streamlit re-runs the whole script on every widget interaction, so the model load and the summarisation call run again even when their inputs didn't change. Fixes: load the model with `@st.cache_resource` so it's created once per process; wrap the summarisation in `@st.cache_data` keyed on the document and parameters, so an unchanged input returns the cached result instantly; put the parameter widgets in an `st.form` so the script re-runs only on submit; and move independent parts of the page into `@st.fragment` functions so they re-run on their own. If the summary genuinely needs recomputing, stream it with `st.write_stream` so the user sees progress."

### Scenario 2: Demo to 200 Concurrent Users
*Interviewer:* "Your Gradio demo of a 7B model on one GPU goes viral; requests are timing out and the GPU runs out of memory. What do you do?"

*Answer:* "First, stop the OOMs: set the event's `concurrency_limit` to what the GPU can hold (often 1-2 for naive `generate` calls) so extra requests wait in Gradio's queue with a visible position instead of crashing. Second, raise throughput: move inference to a server built for concurrency, like vLLM with continuous batching and paged attention (Guide 20), and make the Gradio handler a thin streaming client; or at least use Gradio's `batch=True` so queued requests share a forward pass. Third, reduce work: cap `max_new_tokens`, cache common prompts, and add a queue `max_size` so we reject early instead of timing out. Longer term, a public service with this load needs autoscaling model servers, auth and rate limits, which is past what a demo framework should do."

### Scenario 3: Streamlit or Gradio?
*Interviewer:* "The data team wants a tool to explore model errors on the validation set, and the research team wants to show a new speech model to the public. Which framework for each?"

*Answer:* "Error exploration is a dashboard: filters, tables, charts, drill-down into DataFrames. That's Streamlit's strength, with `st.dataframe`, `st.data_editor` and cached data loading. The speech demo is a model I/O demo: microphone input, audio output, a public URL, and people will want to call it programmatically. That's Gradio: built-in audio components, the request queue to protect the GPU, a free API and client, and one-step hosting on Hugging Face Spaces."

---

## 9. Common Pitfalls & Debugging in Production

### ⚠️ Pitfall 1: Loading the model inside the handler or script body
In Gradio, loading inside `fn` reloads per request; in Streamlit, loading in the script body reloads on every interaction.
*Fix:* Gradio: load at module level. Streamlit: `@st.cache_resource`.

### ⚠️ Pitfall 2: Using `st.cache_data` for unpicklable or huge objects
`cache_data` pickles and copies the return value on every hit: slow for big objects and failing for models or connections.
*Fix:* `cache_resource` for shared objects (models, clients), `cache_data` for data results.

### ⚠️ Pitfall 3: Storing per-user data in globals
A module-level list of chat messages is shared by every user of the app (in both frameworks), leaking one user's conversation into another's.
*Fix:* `st.session_state` in Streamlit; `gr.State` or the Chatbot's history in Gradio.

### ⚠️ Pitfall 4: Streaming deltas instead of accumulated text in Gradio
Yielding only the new token makes the output box show one word at a time, replacing the previous one.
*Fix:* Yield the full text so far on each step (Streamlit's `st.write_stream` is the opposite: it takes deltas and accumulates for you).

### ⚠️ Pitfall 5: Streamlit behind a load balancer drops sessions
Multiple replicas without sticky sessions or WebSocket support make the app reset or hang, because each session's state lives in one server process.
*Fix:* Enable WebSockets and session affinity on the proxy, or run one replica per user group.
