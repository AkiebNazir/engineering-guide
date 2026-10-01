# DeepEval Mastery: Unit Tests for LLM Apps and Agents (plus Inspect and promptfoo)

## 1. The Core Concept (What and Why)

*Why is this tool relevant?* Guide 25 (Ragas) measures one kind of application: RAG. Most LLM code is not only RAG. It is a support chatbot that must stay polite and on-topic over ten turns, an extraction prompt that must return valid JSON, a LangGraph agent (Guide 14) that must call `get_weather` before `convert_units`, a summarizer that must not invent facts. Every prompt tweak, model upgrade or tool change can silently break one of these. You need the LLM equivalent of a unit-test suite: a fixed set of inputs, a set of checks, and a red/green result you can put in CI.

**What is it?**
An **LLM evaluation framework** runs your application over a dataset of test cases and scores each output with **metrics**. Metrics come in two families:
- **Deterministic metrics**: exact match, regex, "is valid JSON", "called these tools in this order", latency, cost. Cheap, fast, reproducible.
- **Model-graded metrics (LLM-as-a-judge)**: a second LLM reads the input, the output and a rubric, and returns a score and a reason. Needed for fuzzy properties like "helpful", "faithful to the context", "stayed in the persona".

**DeepEval** (by Confident AI, Apache-2.0) is a Python framework that packages both families as pytest-style tests: `LLMTestCase` objects, 50+ ready-made metrics (G-Eval, answer relevancy, faithfulness, hallucination, bias, toxicity, tool correctness, task completion, conversation metrics), and a `deepeval test run` command that behaves like `pytest`.

**Why this one?** In 2026 three open-source frameworks cover most real-world usage, and they're good at different things:

| Framework | Shape | Best at | Pick it when |
| --- | --- | --- | --- |
| **DeepEval** | Python library, pytest-native | App-level tests: chat, RAG, agents, multi-turn; many built-in judge metrics | Your app is Python and you want evals next to your unit tests in CI |
| **promptfoo** | CLI + YAML config (Node) | Comparing prompts x models in a matrix; red-teaming/jailbreak scans | You're iterating on prompts, the team isn't Python-first, or you need a security scan |
| **Inspect AI** (UK AI Security Institute) | Python framework | Model/agent *capability* and safety benchmarks: solvers, sandboxed tool use, rich log viewer | You evaluate models themselves (research, model selection, safety evals) |

This guide teaches DeepEval in depth because it's the most widely used Python-first framework for testing *applications* (the thing most engineers ship), and its concepts (test case, metric, threshold, judge) transfer directly to the others. Section 7 shows the same idea in Inspect and promptfoo so you can recognise all three. Hosted platforms (LangSmith, Braintrust, Arize Phoenix, Confident AI's own cloud) add dashboards and production tracing on top of the same ideas.

---

## 2. Setup & Installation

```bash
pip install deepeval          # the library + the `deepeval` CLI
export OPENAI_API_KEY=...     # only needed for LLM-as-judge metrics (default judge is an OpenAI model)
export DEEPEVAL_TELEMETRY_OPT_OUT=1   # DeepEval sends anonymous usage telemetry unless you opt out
```

```python
from importlib.metadata import version

print(f"DeepEval version: {version('deepeval')}")  # 4.x in late 2026
```

*Version note:* DeepEval moves fast. In 4.x the enum of test-case fields is `SingleTurnParams` (older tutorials use `LLMTestCaseParams`, now a deprecated alias) and the OpenAI judge class is `OpenAIModel` (formerly `GPTModel`). If an import fails, check the changelog before assuming the concept changed.

---

## 3. The "Hello World": Deterministic Metrics and a Custom Metric (runs offline)

Start with checks that need no judge at all. Here an extraction prompt must return JSON with three keys. We test three recorded outputs with a built-in metric (`ExactMatchMetric`) and a custom one.

```python
import json
from deepeval import evaluate
from deepeval.evaluate import DisplayConfig
from deepeval.metrics import BaseMetric, ExactMatchMetric
from deepeval.test_case import LLMTestCase


class ValidJsonWithKeys(BaseMetric):
    """Deterministic metric: output must be a JSON object containing the required keys."""

    def __init__(self, required_keys, threshold=1.0):
        self.required_keys = set(required_keys)
        self.threshold = threshold

    def measure(self, test_case, *args, **kwargs):
        try:
            data = json.loads(test_case.actual_output)
        except json.JSONDecodeError as e:
            self.score, self.reason = 0.0, f"not JSON: {e.msg}"
        else:
            missing = self.required_keys - set(data) if isinstance(data, dict) else self.required_keys
            self.score = 1 - len(missing) / len(self.required_keys)
            self.reason = f"missing keys: {sorted(missing)}" if missing else "all keys present"
        self.success = self.score >= self.threshold
        return self.score

    async def a_measure(self, test_case, *args, **kwargs):
        return self.measure(test_case)

    def is_successful(self):
        return self.success

    @property
    def __name__(self):
        return "Valid JSON with keys"


# In a real suite actual_output comes from calling your app; here we paste recorded outputs.
cases = [
    LLMTestCase(input="Extract: Ada, 36, London",
                actual_output='{"name": "Ada", "age": 36, "city": "London"}',
                expected_output='{"name": "Ada", "age": 36, "city": "London"}'),
    LLMTestCase(input="Extract: Bo, 41",
                actual_output='{"name": "Bo", "age": 41}',
                expected_output='{"name": "Bo", "age": 41, "city": null}'),
    LLMTestCase(input="Extract: Cy, 29, Rome",
                actual_output='Sure! Here is the JSON: {"name": "Cy"}',
                expected_output='{"name": "Cy", "age": 29, "city": "Rome"}'),
]

result = evaluate(cases, [ValidJsonWithKeys(["name", "age", "city"]), ExactMatchMetric()],
                  display_config=DisplayConfig(print_results=False, show_indicator=False))

for tr in result.test_results:
    print(tr.success, [(m.name, round(m.score, 2), m.reason) for m in tr.metrics_data])
# True  [('Valid JSON with keys', 1.0, 'all keys present'), ('Exact Match', 1.0, ...)]
# False [('Valid JSON with keys', 0.67, "missing keys: ['city']"), ('Exact Match', 0.0, ...)]
# False [('Valid JSON with keys', 0.0, 'not JSON: Expecting value'), ('Exact Match', 0.0, ...)]
```

The third case is the classic failure: the model wrapped the JSON in chatty prose. A deterministic check catches it for free; don't pay a judge to find it.

### The same thing as a test suite

DeepEval's `assert_test` raises an `AssertionError` when any metric fails, so evals live in ordinary test files:

```python
# test_support_bot.py  ->  run with:  deepeval test run test_support_bot.py   (or plain pytest)
import pytest
from deepeval import assert_test
from deepeval.metrics import ExactMatchMetric
from deepeval.test_case import LLMTestCase


def my_app(question: str) -> str:  # stand-in for your real LLM call
    return {"2+2": "4", "capital of France": "Paris"}.get(question, "I don't know")


@pytest.mark.parametrize("question,expected", [("2+2", "4"), ("capital of France", "Paris")])
def test_answers(question, expected):
    test_case = LLMTestCase(input=question, actual_output=my_app(question), expected_output=expected)
    assert_test(test_case, [ExactMatchMetric()])
```

`deepeval test run` adds LLM-eval conveniences on top of pytest: `-n 4` runs test cases in parallel processes, `-c` reuses cached judge results for unchanged cases, `-r 3` repeats each test to expose flakiness, and it prints a per-metric score table.

---

## 4. Deep Dive: LLM-as-a-Judge Metrics

Deterministic checks can't tell you whether an answer is *helpful* or *correct in substance*. For that you use a judge.

### G-Eval: a rubric turned into a metric

**G-Eval** (Liu et al., 2023) is the workhorse. You write the criteria in plain English; the judge (1) expands them into concrete evaluation steps, (2) reads the fields you named, (3) outputs a score on a small integer scale. When the judge API exposes token log-probabilities, DeepEval weights each possible score by its probability (a probability-weighted average instead of one sampled number), which makes scores smoother and less noisy. The score is normalised to 0-1 and compared to `threshold`.

**Requires network + an API key** (the judge is a hosted LLM):

```python
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.metrics.g_eval import Rubric
from deepeval.models import OpenAIModel
from deepeval.test_case import LLMTestCase, SingleTurnParams

judge = OpenAIModel(model="gpt-4.1", temperature=0)  # pin an exact judge model and version

correctness = GEval(
    name="Correctness",
    # Explicit steps are more stable than a one-line `criteria=`: the judge doesn't re-invent them each run
    evaluation_steps=[
        "List the facts stated in 'expected output'.",
        "Check whether 'actual output' contradicts any of those facts; any contradiction is a heavy penalty.",
        "Missing minor details is a small penalty; extra correct detail is not a penalty.",
        "Ignore style, tone and length.",
    ],
    evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
    rubric=[  # anchors each score band so "7" means the same thing every run
        Rubric(score_range=(0, 2), expected_outcome="Contradicts the expected answer."),
        Rubric(score_range=(3, 6), expected_outcome="Partly correct or missing key facts."),
        Rubric(score_range=(7, 10), expected_outcome="All key facts correct, no contradictions."),
    ],
    model=judge,
    threshold=0.7,
)

test_case = LLMTestCase(
    input="When does the refund window close?",
    actual_output="You can request a refund within 30 days of delivery.",
    expected_output="Refunds are accepted up to 30 days after the item is delivered.",
)
correctness.measure(test_case)
print(correctness.score, correctness.reason)
assert_test(test_case, [correctness])
```

### Parameter Breakdown: `GEval(...)`
- `criteria` vs `evaluation_steps`: give one or the other. `criteria` is shorter, but the judge generates the steps at run time, which adds variance between runs. Write `evaluation_steps` for anything that gates CI.
- `evaluation_params`: which fields the judge sees. Leave out what it shouldn't see (e.g. hide `expected_output` for a reference-free "helpfulness" metric).
- `rubric`: score bands with a description. Reduces "central tendency" (judges love 7/10).
- `threshold`: pass mark on the 0-1 scale. Calibrate it against human labels (Section 6), don't guess.
- `strict_mode=True`: binary output (score 1 or 0). Good for hard rules ("never reveals the system prompt").
- `model`: a model name string or any `DeepEvalBaseLLM`. DeepEval ships wrappers for OpenAI, Azure, Anthropic, Gemini, Bedrock, Ollama, LiteLLM and a `LocalModel`. `OpenAIModel(base_url=...)` points at any OpenAI-compatible server, such as vLLM (Guide 20) or llama.cpp (Guide 21).

### Built-in judge metrics worth knowing

| Metric | Question it answers | Needs |
| --- | --- | --- |
| `AnswerRelevancyMetric` | Does the output address the input? | input, actual_output |
| `FaithfulnessMetric` | Is every claim supported by the retrieved context? (same idea as Ragas) | + retrieval_context |
| `HallucinationMetric` | Does the output contradict the given context? | + context |
| `BiasMetric`, `ToxicityMetric` | Is the output biased/toxic? | actual_output |
| `SummarizationMetric` | Is a summary faithful and complete? | input (source), actual_output |
| `DAGMetric` | A decision tree of small judge questions, each yes/no, combined deterministically | your graph |

`DAGMetric` deserves a note: instead of one big "rate this 1-10" call, you break the rubric into a tree of narrow questions ("Does it have a greeting? Does it mention the order number?"). Narrow yes/no questions are the most reliable thing a judge can answer.

---

## 5. Pro Level: Evaluating Agents and Conversations

An agent can give the right final answer by luck, or the wrong one after a perfect plan with one bad tool call. So agent evals score the **trajectory** (which tools, with which arguments, in which order) as well as the **outcome**.

### Tool correctness: a deterministic trajectory check

`ToolCorrectnessMetric` compares `tools_called` with `expected_tools` by name (optionally also input parameters and order). The comparison itself is plain code; the judge is only consulted if you pass `available_tools` to also grade whether the agent *chose* sensibly among them. The constructor still builds a judge client, so an API key (or a custom `model=`) must be configured.

```python
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

test_case = LLMTestCase(
    input="What's the weather in Paris, in Fahrenheit?",
    actual_output="It is 68F in Paris.",
    tools_called=[ToolCall(name="get_weather", input_parameters={"city": "Paris"}),
                  ToolCall(name="search_web")],
    expected_tools=[ToolCall(name="get_weather", input_parameters={"city": "Paris"}),
                    ToolCall(name="convert_units")],
)
metric = ToolCorrectnessMetric(should_consider_ordering=True, threshold=1.0)
metric.measure(test_case)
print(metric.score)   # 0.5: 1 of 2 expected tools called (convert_units is missing)
print(metric.reason)
```

Note what the score does *not* do: calling an extra, unnecessary tool (`search_web` here) isn't penalised; with `convert_units` added, the same case scores 1.0. If wasted calls matter (cost, side effects), add your own check on `len(tools_called)` or use a step-efficiency metric.

### Task completion from a trace (requires network)

For real agents you don't hand-build `tools_called`. You decorate the agent's functions with `@observe`; DeepEval records a trace (agent span, tool spans, LLM spans) and `TaskCompletionMetric` asks the judge "given this trace, did the agent accomplish what the user asked?".

```python
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.metrics import TaskCompletionMetric
from deepeval.tracing import observe


@observe(type="tool")
def get_weather(city: str) -> dict:
    return {"city": city, "celsius": 20}          # call your real API here


@observe(type="tool")
def convert_units(celsius: float) -> float:
    return celsius * 9 / 5 + 32


@observe(type="agent")
def weather_agent(question: str) -> str:
    # In a real agent an LLM decides which tools to call (Guide 14 LangGraph, Guide 15 CrewAI)
    weather = get_weather("Paris")
    return f"It is {convert_units(weather['celsius']):.0f}F in Paris."


dataset = EvaluationDataset(goldens=[Golden(input="What's the weather in Paris, in Fahrenheit?")])
for golden in dataset.evals_iterator(metrics=[TaskCompletionMetric(threshold=0.7)]):
    weather_agent(golden.input)       # each call is traced and scored
```

### Multi-turn conversations

A chatbot can answer every turn well and still fail the conversation: forget the user's name from turn 2, drift off-topic, or break its persona. Use `ConversationalTestCase` (a list of `Turn`s) with conversation metrics (`ConversationalGEval`, `KnowledgeRetentionMetric`, `RoleAdherenceMetric`, `ConversationCompletenessMetric`). **Requires network**:

```python
from deepeval.metrics import ConversationalGEval
from deepeval.test_case import ConversationalTestCase, MultiTurnParams, Turn

convo = ConversationalTestCase(
    chatbot_role="A polite airline support agent that never promises compensation.",
    turns=[
        Turn(role="user", content="My flight LH123 was cancelled. I'm Maya."),
        Turn(role="assistant", content="Sorry to hear that, Maya. I can rebook you on LH125 tonight."),
        Turn(role="user", content="Will I get 600 euros?"),
        Turn(role="assistant", content="You'll definitely get 600 euros, Maya!"),
    ],
)
no_promises = ConversationalGEval(
    name="No compensation promises",
    criteria="The assistant must never promise or guarantee compensation amounts.",
    evaluation_params=[MultiTurnParams.ROLE, MultiTurnParams.CONTENT],
    threshold=0.8,
)
no_promises.measure(convo)
print(no_promises.score, no_promises.reason)   # expect a low score: turn 4 breaks the rule
```

To generate the conversations themselves, DeepEval has a conversation simulator (an LLM playing the user with a given goal and persona), which is how you get hundreds of multi-turn test cases without writing them by hand.

---

## 6. Pro Level: LLM-as-a-Judge Pitfalls (and how to measure them)

A judge is a model, so it has biases, and its scores are measurements with error. The known failure modes:

1. **Position bias**: in pairwise "A or B?" comparisons, judges favour one slot (often the first). *Fix:* judge both orders; count a win only if both orders agree, otherwise a tie.
2. **Verbosity bias**: longer answers score higher even with less substance. *Fix:* say "ignore length" in the steps, add length-controlled comparisons, and check score vs length correlation.
3. **Self-preference**: a judge rates outputs from its own model family higher. *Fix:* use a judge from a different family than the system under test, or a panel of judges.
4. **Central tendency and leniency**: on a 1-10 scale most scores land at 7-8; "is this OK?" gets "yes". *Fix:* binary or 3-point scales, anchored rubrics, narrow questions (DAG).
5. **Prompt and version sensitivity**: rewording the rubric or a silent judge-model update shifts every score. *Fix:* pin the exact judge version and treat the judge prompt as code (reviewed, versioned). Re-baseline when either changes.
6. **Answer-key leakage and reference bias**: a judge shown the reference answer penalises correct answers that are phrased differently. *Fix:* grade facts, not wording ("contradicts?" rather than "matches?").
7. **Noise, then over-reading small deltas**: a 2-point improvement on 50 cases is usually noise. *Fix:* confidence intervals, more cases, repeated runs.
8. **Unvalidated judges**: nobody checked that the judge agrees with humans. *Fix:* label 100-200 cases by hand and measure agreement with **Cohen's kappa**, not raw percent agreement.

The lab below simulates three of these with NumPy so you can see the numbers move (runs offline):

```python
import numpy as np

rng = np.random.default_rng(0)

# ---------- 1. Position bias in pairwise judging ----------
n = 400
gap = rng.normal(0, 1, n)            # true quality(A) - quality(B); > 0 means A is better
a_better = gap > 0

def judge_prefers_first(gap_first_minus_second, first_bonus=0.5, noise=0.7):
    """A simulated judge: sees the quality gap through noise, plus a bonus for whatever is shown first."""
    return gap_first_minus_second + first_bonus + rng.normal(0, noise, n) > 0

a_wins_when_first = judge_prefers_first(gap)       # order (A, B)
a_wins_when_second = ~judge_prefers_first(-gap)    # order (B, A): judge prefers B -> A loses
consistent = a_wins_when_first == a_wins_when_second

print(f"Picks A when A is shown first : {a_wins_when_first.mean():.0%}  (truth: {a_better.mean():.0%})")
print(f"Picks A when A is shown second: {a_wins_when_second.mean():.0%}")
print(f"Position consistency          : {consistent.mean():.0%}")
print(f"Accuracy, one order only      : {(a_wins_when_first == a_better).mean():.0%}")
print(f"Accuracy, consistent pairs    : {(a_wins_when_first[consistent] == a_better[consistent]).mean():.0%}"
      f" on {consistent.sum()} pairs; the other {n - consistent.sum()} are ties")

# ---------- 2. Agreement with humans: raw % vs Cohen's kappa ----------
def cohens_kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    p_observed = (a == b).mean()
    p_chance = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return (p_observed - p_chance) / (1 - p_chance)

human = rng.random(300) < 0.85                          # 85% of answers are acceptable
lenient_judge = np.ones(300, dtype=bool)                # says "pass" to everything
careful_judge = np.where(rng.random(300) < 0.9, human, ~human)  # agrees with humans 90% of the time

for name, j in [("lenient", lenient_judge), ("careful", careful_judge)]:
    print(f"{name:8} judge: raw agreement {(j == human).mean():.0%}, kappa {cohens_kappa(j, human):.2f}")

# ---------- 3. Is prompt v2 really better? Paired bootstrap ----------
def compare(m):
    v1 = rng.random(m) < 0.78                                   # pass/fail per case, prompt v1
    # v2 runs on the SAME cases: it keeps most passes and fixes some failures
    v2 = np.where(v1, rng.random(m) > 0.04, rng.random(m) < 0.30)
    diffs = np.empty(5_000)
    for i in range(diffs.size):
        idx = rng.integers(0, m, m)                             # resample cases, keep pairs together
        diffs[i] = v2[idx].mean() - v1[idx].mean()
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    verdict = "v2 is better" if lo > 0 else "not proven (CI includes 0)"
    print(f"n={m:5}: v1={v1.mean():.3f} v2={v2.mean():.3f} diff={v2.mean() - v1.mean():+.3f}"
          f"  95% CI [{lo:+.3f}, {hi:+.3f}]  -> {verdict}")

compare(50)
compare(1_000)
```

Output (seeded, so yours matches):

```text
Picks A when A is shown first : 62%  (truth: 47%)
Picks A when A is shown second: 34%
Position consistency          : 67%
Accuracy, one order only      : 79%
Accuracy, consistent pairs    : 95% on 268 pairs; the other 132 are ties
lenient  judge: raw agreement 83%, kappa 0.00
careful  judge: raw agreement 89%, kappa 0.66
n=   50: v1=0.800 v2=0.820 diff=+0.020  95% CI [-0.060, +0.100]  -> not proven (CI includes 0)
n= 1000: v1=0.784 v2=0.814 diff=+0.030  95% CI [+0.009, +0.050]  -> v2 is better
```

Read it like this:
- A judge with a first-slot bonus picks A 62% of the time when A is first and 34% when A is second, though A is truly better in 47% of pairs. Swapping and keeping only agreeing verdicts raises accuracy from 79% to 95%, at the cost of a third of the pairs becoming ties.
- The "lenient" judge agrees with humans 83% of the time, which sounds fine, yet its kappa is 0.00: it has learned nothing, it just says "pass" and the data is 85% passes. Always report kappa (a common rule of thumb reads 0.6-0.8 as substantial agreement).
- The same +2-3 point improvement is noise on 50 cases and a real result on 1,000. Pair the comparison (same cases for both versions), since paired tests cancel out per-case difficulty.

---

## 7. The Same Ideas in Inspect AI and promptfoo

### Inspect AI (runs offline with a mock model)

Inspect's vocabulary: a **Task** = a **dataset** of `Sample`s + a **solver** chain (system prompt, generate, tool use, agent loops) + a **scorer**. Every run writes a log file you can browse with `inspect view`. The built-in `mockllm/model` provider lets you test the eval plumbing without an API key.

```python
from inspect_ai import Task, eval, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ModelOutput, ModelUsage, get_model
from inspect_ai.scorer import includes
from inspect_ai.solver import generate, system_message


@task
def capitals():
    return Task(
        dataset=[
            Sample(input="What is the capital of France? One word.", target="Paris"),
            Sample(input="What is the capital of Japan? One word.", target="Tokyo"),
            Sample(input="What is the capital of Australia? One word.", target="Canberra"),
        ],
        solver=[system_message("You are a terse geography expert."), generate()],
        scorer=includes(),  # pass if the target string appears in the output
    )


# Offline stand-in for a real model: answers by looking at the question.
# (It gets Australia wrong on purpose, like many small models do.)
CANNED = {"France": "Paris.", "Japan": "Tokyo", "Australia": "Sydney"}

def fake_model(messages, tools, tool_choice, config):
    question = messages[-1].text
    answer = next(a for country, a in CANNED.items() if country in question)
    out = ModelOutput.from_content(model="mockllm", content=answer)
    out.usage = ModelUsage(input_tokens=20, output_tokens=2, total_tokens=22)  # skip token counting
    return out

mock = get_model("mockllm/model", custom_outputs=fake_model)
log = eval(capitals(), model=mock, log_dir="./inspect-logs", display="none")[0]

print(log.status)                                   # success
for score in log.results.scores:
    print(score.name, {k: round(v.value, 3) for k, v in score.metrics.items()})
    # includes {'accuracy': 0.667, 'stderr': 0.333}
for s in log.samples:
    print(f"{s.target!s:9} <- {s.output.completion!r:9} {s.scores['includes'].value}")  # C / C / I
```

Against a real model it's the same task: `inspect eval capitals.py --model openai/gpt-4.1-mini` (network). Swap `includes()` for `model_graded_qa()` to use a judge, and use Inspect's agent solvers with a Docker sandbox when the model must run code or tools safely. Note that Inspect reports `stderr` next to accuracy by default, which nudges you toward reading scores as estimates.

### promptfoo (CLI + YAML; requires Node and network)

promptfoo evaluates a matrix of prompts x providers x test cases from one config file, then shows a side-by-side web view.

```yaml
# promptfooconfig.yaml  ->  npx promptfoo@latest eval   then   npx promptfoo@latest view
description: Support bot, prompt v1 vs v2
prompts:
  - file://prompts/support_v1.txt
  - file://prompts/support_v2.txt
providers:
  - openai:gpt-4.1-mini
  - openai:gpt-4.1
defaultTest:
  assert:
    - type: not-icontains
      value: "as an ai"
tests:
  - vars:
      question: "How do I reset my password?"
    assert:
      - type: icontains          # deterministic
        value: "reset link"
      - type: llm-rubric         # LLM-as-judge
        value: "Gives numbered steps and does not ask for the current password."
      - type: latency
        threshold: 3000          # ms
```

Its other headline feature is `promptfoo redteam`, which generates adversarial inputs (prompt injection, jailbreaks, PII extraction, harmful-content probes) against your app and reports which ones got through; it pairs naturally with Guide 28 (guardrails).

---

## 8. Production: Evals in CI and on Live Traffic

1. **Golden dataset.** Start with 50-200 real, anonymised user inputs covering the main intents and the known failure cases; grow it every time production finds a new bug (every bug becomes a test case). Version it with the code.
2. **Tiered suites.** Fast deterministic checks on every commit; the judge suite (costs money, takes minutes) on PRs that touch prompts, models or retrieval; a large nightly run with repeats for trend lines.
3. **Gate on regressions, not absolutes.** Compare to the main-branch baseline with a paired test and a tolerance; fail the PR if a metric drops beyond noise.
4. **Cache judge calls.** Unchanged test case + unchanged metric = reuse the score (`deepeval test run -c`), which cuts CI cost sharply.
5. **Online evaluation.** Sample a small percentage of production traffic, run reference-free metrics (relevancy, toxicity, PII leakage, task completion from traces) asynchronously, and alert on drift. Never put a slow judge on the synchronous request path; that's what guardrails (Guide 28) are for, with small fast classifiers.
6. **Track cost and latency as metrics.** A prompt that's 1% better and 3x slower is usually a regression.

---

## 9. MAANG Interview Scenarios

### Scenario 1: Designing an Eval Suite for an Agent
*Interviewer:* "We're launching a travel-booking agent with six tools. How do you know it works, and how do you stop regressions?"

*Answer:* "I'd evaluate three levels. First, the **components**: each tool has normal unit tests, and the planner's tool choice has a deterministic check: for 100 golden requests I record the expected tool sequence and arguments and score `tools_called` against `expected_tools`. That's cheap and exact. Second, the **outcome**: a task-completion judge reads the trace and decides whether the user's goal was met, validated against about 150 human-labelled traces with Cohen's kappa before I trust it. Third, **safety and policy**: deterministic assertions for hard rules (never books without explicit confirmation, never shows another user's data) plus red-team inputs. The deterministic tier runs on every commit; the judge tier runs on PRs that touch prompts, tools or the model, gated on a paired comparison against main with confidence intervals, not a raw threshold. In production I sample traces for the same reference-free metrics and add every incident to the golden set."

### Scenario 2: The Judge Says We Improved
*Interviewer:* "A teammate switched the model and G-Eval 'helpfulness' went from 0.81 to 0.86 on 40 examples. Ship it?"

*Answer:* "Not yet. Four checks. Is it significant? With 40 cases the confidence interval on a 5-point difference almost certainly includes zero; I'd run a paired bootstrap and probably grow the set. Is the judge biased toward the new model? If the judge and the new model are the same family, self-preference can explain it; I'd re-judge with a different family. Did length change? If the new model writes 40% more, verbosity bias may be the whole effect, so I'd check score against length. Did anything else regress? Latency, cost, refusal rate and the deterministic checks must hold too. If it survives all four, ship behind a flag and confirm with an online A/B on a real user metric."

### Scenario 3: Why Not Just Use Exact Match?
*Interviewer:* "LLM judges are expensive and noisy. Why not only exact match or BLEU/ROUGE?"

*Answer:* "Use deterministic metrics wherever the answer has a canonical form: classification labels, JSON fields, tool names, numbers, SQL results. They're free, reproducible and should be the majority of the suite. But for open-ended text, n-gram overlap metrics like BLEU and ROUGE correlate poorly with human judgement: 'refunds close 30 days after delivery' and 'you have a month from delivery to get your money back' share few n-grams and mean the same thing. That's where a judge, validated against human labels, is worth its cost. The skill is choosing the cheapest metric that measures the property you care about."

---

## 10. Common Pitfalls & Debugging in Production

### ⚠️ Pitfall 1: Judging what code could check
Paying a judge to decide "is this valid JSON?" or "did it mention the order ID?" is slow, costly, and less reliable than `json.loads` or a regex.
*Fix:* Deterministic metrics first; reserve judges for properties only language understanding can assess.

### ⚠️ Pitfall 2: Flaky CI from a stochastic judge
The same case passes, then fails, with no code change.
*Fix:* `temperature=0` on the judge, explicit `evaluation_steps` instead of `criteria`, binary or anchored rubrics, a small tolerance band around the threshold, and `-r 3` repeats to find unstable cases.

### ⚠️ Pitfall 3: Evaluating on the examples you tuned on
If the prompt was iterated against the same 30 cases that form the eval set, the score is overfit.
*Fix:* Keep a held-out split that nobody looks at during prompt iteration, like a test set in classical ML (Guide 03).

### ⚠️ Pitfall 4: Silent judge-model upgrades
You call "the latest" judge alias; the provider updates it; every score shifts by 0.05 overnight and it looks like your app changed.
*Fix:* Pin exact model versions for the judge, record judge model and prompt version with every result, and re-baseline deliberately.

### ⚠️ Pitfall 5: Missing test-case fields
A metric that needs `retrieval_context` or `expected_output` raises (or, with `skip_on_missing_params`, silently skips) when the field is empty, so a green run may have tested nothing.
*Fix:* Check the number of *scored* cases in the report, not only the pass rate, and fail the run if it's below the dataset size.
