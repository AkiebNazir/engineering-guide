# Day 109: Reasoning Models (RL with Verifiable Rewards, GRPO & Test-Time Compute)

Welcome to Day 109. In September 2024 OpenAI released **o1**, a model that "thinks" for seconds or minutes before answering and jumped far ahead on competition math and coding. In January 2025 DeepSeek published **DeepSeek-R1** with open weights and a paper explaining how: plain reinforcement learning, with rewards computed by a program instead of a human, on a strong base model. Within months every frontier lab shipped a "thinking" mode.

Day 115 will cover the *prompting* tricks (Chain-of-Thought, Self-Consistency, Tree of Thoughts, ReAct) that ask an ordinary model to reason. Today is about how **reasoning models are actually trained and served**: RL with verifiable rewards (RLVR), the GRPO algorithm, test-time compute scaling, and thinking budgets.

> **Where this fits:** Days 101–103 built RLHF with PPO and a learned reward model, Day 104 replaced it with DPO, and Day 105 used AI feedback. Today swaps the learned reward for a *verifier* and PPO for GRPO. Tomorrow (Day 110) shows how the long reasoning traces these models produce are distilled into small models. Domain adaptation and continued pre-training, which this slot used to hold, are covered on Day 75.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. What Makes a "Reasoning Model" Different
A reasoning model is an ordinary Transformer that has been trained with RL to write a long internal chain of thought (often thousands of tokens, wrapped in something like `<think>...</think>`) **before** its final answer. Inside that trace it tries approaches, checks intermediate results, notices mistakes ("wait, that's wrong...") and backtracks.

Nothing about the architecture changed. What changed is the training signal: the model is rewarded only for getting the **final answer right**, and it discovers that thinking longer and checking its work raises that reward.

That gives two new scaling axes, both reported by OpenAI with o1:
- **Train-time RL compute:** more RL steps → better accuracy.
- **Test-time compute:** letting the model think for more tokens at inference → better accuracy, smoothly, on a log scale.

Analogy: a standard chat model is a student who must answer each exam question instantly. A reasoning model is the same student allowed scratch paper and time, who has also been trained, through thousands of graded practice exams, to actually *use* the scratch paper well.

### 2. From RLHF to RLVR: Rewards You Can Compute
In RLHF (Days 101–103) the reward comes from a **learned reward model** trained on human preferences. That works for "be helpful and polite", but a reward model can be fooled: the policy learns to write answers that *look* good to the reward model (reward hacking, Day 102).

**RL with Verifiable Rewards (RLVR)**, a term popularized by AI2's Tülu 3 (2024), uses tasks where correctness can be checked by a program:
- **Math:** compare the final answer (e.g., the content of `\boxed{...}`) with the known solution, after normalization.
- **Code:** run the generated code against unit tests in a sandbox.
- **Logic puzzles, SQL, formal proofs:** execute or check with a solver or proof assistant.
- **Format rewards:** a small bonus for putting reasoning inside the expected tags and the answer in a parseable place.

Because the reward is a rule, it is cheap, it scales to millions of problems, and it is much harder to hack than a neural reward model. It is not impossible to hack: a coding policy can learn to special-case the visible tests or to exit before assertions run. Hidden tests and sandbox hardening are part of the reward design.

### 3. GRPO: PPO Without the Critic
PPO (Day 101) needs a **value network** (the critic), usually as big as the policy, to estimate a baseline for each token. For a 70B policy that doubles the memory and adds a hard-to-train model.

**GRPO** (Group Relative Policy Optimization, from DeepSeekMath, 2024) removes the critic:
1. For each prompt $q$, sample a **group** of $G$ completions $o_1, \dots, o_G$ from the current policy (e.g., $G = 8$–$64$).
2. Score each with the verifier: rewards $r_1, \dots, r_G$.
3. The **group-relative advantage** of every token in completion $i$ is
$$\hat A_i = \frac{r_i - \text{mean}(r_1..r_G)}{\text{std}(r_1..r_G)}$$
The other samples for the *same prompt* are the baseline. Better than your siblings: pushed up. Worse: pushed down.
4. Update with PPO's clipped objective plus a KL penalty to a frozen reference model:
$$\mathcal{J}(\theta) = \mathbb{E}\Big[\frac{1}{G}\sum_i \frac{1}{|o_i|}\sum_t \min\big(\rho_{i,t}\hat A_i,\ \text{clip}(\rho_{i,t}, 1-\epsilon, 1+\epsilon)\hat A_i\big)\Big] - \beta\, D_{KL}(\pi_\theta \,\|\, \pi_{ref})$$
where $\rho_{i,t} = \frac{\pi_\theta(o_{i,t}\mid q, o_{i,<t})}{\pi_{\theta_{old}}(o_{i,t}\mid q, o_{i,<t})}$ is the probability ratio (Day 101). The KL is estimated per token with the low-variance "k3" estimator $\frac{\pi_{ref}}{\pi_\theta} - \log\frac{\pi_{ref}}{\pi_\theta} - 1$.

Important consequences:
- **No signal when the whole group agrees.** If all 16 samples are right (too easy) or all wrong (too hard), every advantage is 0. Training data must sit in the model's zone of partial success, so pipelines filter or re-sample problems by pass rate (DAPO's "dynamic sampling" does this online).
- **The expensive part is generation, not the gradient step.** Sampling $G$ long completions per prompt dominates cost, so RL systems pair a fast inference engine (vLLM/SGLang, Day 92) for rollouts with a training framework (FSDP/Megatron) and sync weights between them.
- **Known biases, known fixes.** Follow-up work tuned GRPO: **DAPO** (asymmetric "clip-higher", dynamic sampling, token-level loss averaging, a soft penalty for overlong answers) and **Dr. GRPO** (drops the per-sequence length normalization and the std division, which were shown to bias the model toward long wrong answers). RLOO and REINFORCE++ are other critic-free baselines.

### 4. The DeepSeek-R1 Recipe (Know It for Interviews)
**R1-Zero** was the experiment: take the DeepSeek-V3 base model, skip SFT entirely, and run GRPO with only rule-based rewards (accuracy + format). Accuracy on AIME math rose from about 16% to about 71% pass@1 during training (numbers from the paper), and the average response length grew steadily from hundreds to thousands of tokens, without anyone asking for longer answers. The paper highlighted an "aha moment" where the model began re-evaluating its own steps. (Later work found that base models already show some self-reflection, so how "emergent" this is remains debated; the length growth and accuracy gains are not.) R1-Zero's problems were practical: poor readability and mixed languages in the reasoning.

**R1** fixed that with four stages:
1. **Cold-start SFT** on a few thousand curated long-CoT examples with a readable format.
2. **Reasoning RL** (GRPO, verifiable rewards) plus a language-consistency reward.
3. **Rejection sampling + SFT:** generate many answers with the RL checkpoint, keep the correct and readable ones (~600K reasoning samples), add ~200K non-reasoning samples (writing, QA), and fine-tune the base model again on all of it.
4. **RL for all scenarios:** verifiable rewards for reasoning tasks plus reward models for helpfulness and harmlessness.

Two findings from the paper that interviewers like:
- **Distillation beats small-scale RL.** Fine-tuning Qwen and Llama models (1.5B–70B) with plain SFT on R1's ~800K samples produced much stronger small reasoners than running RL on those small models directly. Big-model RL discovers the behavior; SFT transfers it (Day 110).
- **What did not work for them:** process reward models (hard to define and label steps, and prone to reward hacking) and Monte-Carlo Tree Search over tokens (the search space is too large). Outcome rewards plus lots of sampling won.

### 5. Test-Time Compute: Sequential vs Parallel
There are two ways to spend more compute on one question at inference:
- **Sequential (think longer):** one long chain of thought that revises itself. This is what RL-trained reasoning models do natively.
- **Parallel (sample more):** generate $N$ independent answers and aggregate them. Majority vote (Self-Consistency, Day 115), or **best-of-N** with a verifier: an outcome reward model, a process reward model that scores each step, or real unit tests for code.

Research results worth quoting (approximately):
- Snell et al. (2024): allocating test-time compute *adaptively by difficulty* can beat a model with many times more parameters on problems the small model can partly solve. Very hard problems still need a better base model.
- **s1** (Muennighoff et al., 2025): fine-tune on only 1,000 curated reasoning traces, then control thinking length at inference with **budget forcing**: to make the model think longer, suppress the end-of-thinking token and append "Wait"; to make it stop, force the end-of-thinking token.
- **Majority voting has a ceiling:** it only helps when the correct answer is the most common one. If the model makes the *same* mistake most of the time, more samples make you more confidently wrong. Today's lab shows this.

### 6. Thinking Budgets in Products
Reasoning is now a product knob, and the knobs keep evolving, so check current docs:
- **OpenAI** exposes a *reasoning effort* setting (low/medium/high) on its reasoning models; the reasoning tokens are hidden but billed as output tokens.
- **Anthropic** first shipped "extended thinking" with an explicit thinking-token budget, then moved its newer models to *adaptive* thinking, where the model decides how much to think and the developer sets an *effort* level (low through max).
- **Google Gemini** 2.5-era models take a thinking budget in tokens.
- **Open models** such as Qwen3 ship one set of weights with both a thinking and a non-thinking mode, switched through the chat template.

Design rules: route easy traffic (classification, extraction, chit-chat) to low effort or no thinking, and hard traffic (multi-step math, planning, difficult code) to high effort. Always cap output tokens. Measure **cost per solved task**, not cost per request: a cheaper call that fails and needs a retry is not cheaper.

### 7. Serving Reasoning Models
Thinking changes the serving profile (Days 151–152):
- **Decode dominates.** A 300-token answer may come with 5,000 thinking tokens. Throughput is limited by decode speed and KV-cache capacity, so FP8 KV cache, speculative decoding and big batches matter more.
- **Latency UX.** Users stare at a spinner for tens of seconds. Stream a reasoning summary or progress indicator, and give the user a way to stop.
- **Parsing.** Open reasoning models emit `<think>...</think>`. Engines have reasoning parsers (e.g., vLLM's `--reasoning-parser`) that split reasoning from the answer so your JSON parser only sees the answer.
- **Multi-turn.** Chat templates of open reasoning models typically drop earlier turns' reasoning from the context to save tokens; follow the model's template rather than improvising. Hosted APIs have their own rules for passing thinking blocks back, especially around tool calls.

### 8. Failure Modes
- **Overthinking:** thousands of tokens spent on "what is 2+2". Fixes: difficulty routing, effort settings, length penalties during RL.
- **Underthinking:** switching approaches too early on hard problems without finishing any of them.
- **Reward hacking:** gaming weak unit tests or the answer extractor. Use hidden tests, strict parsing and sandboxing.
- **Unfaithful reasoning:** the visible chain of thought is not guaranteed to reflect how the model reached its answer. Treat it as a useful, imperfect monitoring signal, not proof.
- **Contamination:** public math benchmarks leak into training data (Day 74's decontamination). Report results on fresh competitions and private sets.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

### Part 1: GRPO and Test-Time Scaling From Scratch (pure Python)
A real GRPO run needs GPUs. The *algorithm* does not. We shrink the "model" to one decision: **how many extra checking passes to spend** before answering an addition problem. More passes cost tokens but, with a majority vote over the attempts, make the answer more reliable. The reward is verifiable (the sum is right or wrong) minus a small cost per token. The policy starts like a base model that almost always answers immediately.

Watch whether GRPO discovers, on its own, that hard problems deserve more thinking and easy ones don't.

Create a file named `grpo_lab.py`:

```python
import math
import random
from collections import Counter

random.seed(0)

# ---------- The environment: problems with a VERIFIABLE answer ----------
BUDGETS = [0, 2, 4, 8]             # extra "thinking" passes the policy may spend
DIGITS = {"easy": 2, "hard": 8}    # easy = 2-digit sums, hard = 8-digit sums
DIGIT_ERROR = {"easy": 0.005, "hard": 0.05}   # per-digit slip rate of one attempt
TOKEN_COST = 0.0003                # reward penalty per "thinking token"


def make_problem(kind):
    n = DIGITS[kind]
    a, b = random.randrange(10 ** (n - 1), 10 ** n), random.randrange(10 ** (n - 1), 10 ** n)
    return kind, a, b


def noisy_attempt(kind, a, b):
    """One pass of a fallible solver: every digit of the answer can slip."""
    digits = list(str(a + b))
    for i in range(len(digits)):
        if random.random() < DIGIT_ERROR[kind]:
            digits[i] = str((int(digits[i]) + random.randint(1, 9)) % 10)
    return int("".join(digits))


def solve(kind, a, b, extra_passes):
    """'Thinking longer' = more independent passes, then keep the most common answer
    (a crude stand-in for the self-checking an RL-trained model learns to do)."""
    attempts = [noisy_attempt(kind, a, b) for _ in range(1 + extra_passes)]
    answer = Counter(attempts).most_common(1)[0][0]
    tokens = (1 + extra_passes) * 10 * len(str(a + b))
    return answer, tokens


def verifier_reward(a, b, answer, tokens):
    """RLVR: the reward is a rule, not a learned reward model. Correct or not."""
    return (1.0 if answer == a + b else 0.0) - TOKEN_COST * tokens


# ---------- The policy: a softmax over thinking budgets, per difficulty ----------
def softmax(logits):
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    s = sum(exps)
    return [e / s for e in exps]


def sample(probs):
    r, acc = random.random(), 0.0
    for i, p in enumerate(probs):
        acc += p
        if r < acc:
            return i
    return len(probs) - 1


# ---------- GRPO ----------
def grpo_train(steps=300, group_size=16, lr=0.5, clip=0.2, beta=0.02, inner_epochs=4):
    # Start like a base model: it mostly answers straight away without checking.
    logits = {k: [2.0, 0.0, 0.0, 0.0] for k in DIGITS}
    ref = {k: softmax(v) for k, v in logits.items()}            # frozen reference policy
    for step in range(steps + 1):
        if step % 100 == 0:
            report(step, logits)
        kind = random.choice(list(DIGITS))
        _, a, b = make_problem(kind)
        old = softmax(logits[kind])

        # 1. Sample a GROUP of completions for the same prompt and score each one.
        actions = [sample(old) for _ in range(group_size)]
        rewards = [verifier_reward(a, b, *solve(kind, a, b, BUDGETS[i])) for i in actions]

        # 2. Group-relative advantage: no value network, the group mean is the baseline.
        mean = sum(rewards) / len(rewards)
        std = (sum((r - mean) ** 2 for r in rewards) / len(rewards)) ** 0.5
        if std < 1e-8:
            continue                                   # all equal: no learning signal
        adv = [(r - mean) / std for r in rewards]

        # 3. PPO-style clipped update + KL penalty to the reference policy.
        for _ in range(inner_epochs):
            probs = softmax(logits[kind])
            grad = [0.0] * len(BUDGETS)
            for act, A in zip(actions, adv):
                ratio = probs[act] / old[act]
                clipped = (A > 0 and ratio > 1 + clip) or (A < 0 and ratio < 1 - clip)
                pg = 0.0 if clipped else A * ratio
                kl = beta * (1 - ref[kind][act] / probs[act])   # d/dlogp of the k3 KL estimator
                coef = (pg - kl) / group_size
                for j in range(len(BUDGETS)):
                    grad[j] += coef * ((1.0 if j == act else 0.0) - probs[j])
            logits[kind] = [l + lr * g for l, g in zip(logits[kind], grad)]

    return logits


def evaluate(policy_logits, kind, n=400):
    correct, tokens = 0, 0
    probs = softmax(policy_logits[kind])
    for _ in range(n):
        _, a, b = make_problem(kind)
        ans, t = solve(kind, a, b, BUDGETS[sample(probs)])
        correct += ans == a + b
        tokens += t
    return correct / n, tokens / n


def report(step, logits):
    parts = []
    for kind in DIGITS:
        probs = softmax(logits[kind])
        exp_budget = sum(p * b for p, b in zip(probs, BUDGETS))
        acc, tok = evaluate(logits, kind, 200)
        parts.append(f"{kind}: E[passes]={exp_budget:4.2f} acc={acc:.2f} tokens={tok:5.0f}")
    print(f"step {step:3d} | " + " | ".join(parts))


# ---------- Test-time compute: parallel sampling + majority vote ----------
def maj_at_n(p_correct, p_common_wrong, n, trials=4000):
    """One solver sample is: correct with p_correct, a single popular wrong answer
    with p_common_wrong, otherwise a random scattered wrong answer."""
    hits = 0
    for _ in range(trials):
        votes = Counter()
        for _ in range(n):
            r = random.random()
            if r < p_correct:
                votes["right"] += 1
            elif r < p_correct + p_common_wrong:
                votes["popular-wrong"] += 1
            else:
                votes[f"noise-{random.randrange(10**6)}"] += 1
        top = max(votes.values())
        winners = [k for k, v in votes.items() if v == top]
        hits += random.choice(winners) == "right"          # break ties at random
    return hits / trials


def main():
    print("== GRPO with a verifiable reward (reward = correct - token cost) ==")
    grpo_train()

    print("\n== Test-time scaling: majority@N ==")
    print("   N   solver A (40% right, errors scattered)   solver B (40% right, 45% same wrong answer)")
    for n in [1, 4, 16, 64]:
        print(f"  {n:3d}   {maj_at_n(0.40, 0.10, n):.2f}"
              f"                                     {maj_at_n(0.40, 0.45, n):.2f}")


if __name__ == "__main__":
    main()
```

Expected output (Python 3.11+, fixed seed; other seeds converge to the same pattern):
```text
== GRPO with a verifiable reward (reward = correct - token cost) ==
step   0 | easy: E[passes]=1.35 acc=0.99 tokens=   54 | hard: E[passes]=1.35 acc=0.71 tokens=  188
step 100 | easy: E[passes]=0.04 acc=0.98 tokens=   27 | hard: E[passes]=3.32 acc=0.87 tokens=  377
step 200 | easy: E[passes]=0.02 acc=0.98 tokens=   26 | hard: E[passes]=3.60 acc=0.92 tokens=  414
step 300 | easy: E[passes]=0.02 acc=0.99 tokens=   26 | hard: E[passes]=3.42 acc=0.88 tokens=  376

== Test-time scaling: majority@N ==
   N   solver A (40% right, errors scattered)   solver B (40% right, 45% same wrong answer)
    1   0.40                                     0.39
    4   0.61                                     0.43
   16   0.97                                     0.42
   64   1.00                                     0.32
```

### Key Takeaways from Code:
1. **Adaptive thinking emerges from the reward alone:** nobody told the policy that 8-digit sums are harder. Within ~100 updates it cut thinking on easy problems to almost zero (it was already right, so thinking only cost tokens) and roughly tripled it on hard ones, lifting hard accuracy from ~0.71 to ~0.9. This is the R1-Zero "response length grows" effect in miniature, and the reason reasoning models spend compute unevenly.
2. **The group is the baseline:** `adv = (r - mean) / std` over 16 samples of the *same* problem replaces PPO's value network. When all samples get the same reward, `std` is 0 and the step is skipped: no learning signal. That is why training sets are filtered to problems the model sometimes, but not always, solves.
3. **Clipping and KL keep updates small:** the ratio `probs[act] / old[act]` is clipped exactly as in PPO (Day 101), and the KL term pulls toward the reference policy (which prefers answering immediately). Try `beta=1.0`: the hard-problem budget barely moves from where it started, because staying close to the reference outweighs the reward.
4. **The token cost shapes behavior:** set `TOKEN_COST = 0` and the policy drifts toward maximum thinking everywhere (about 8 passes on hard problems and nearly 4 on easy ones, where it was already right). That is overthinking, and it is why production RL adds length penalties or budget-aware rewards.
5. **Majority voting only fixes random errors:** solver A's mistakes are scattered, so 16 votes take it from 40% to 97%. Solver B makes the *same* mistake 45% of the time, so more votes lock in the wrong answer (0.39 → 0.32). Parallel sampling needs either diverse errors or a real verifier (tests, a checker, a trained reward model).

### Part 2: The Same Algorithm on a Real Model (GPU)
Hugging Face TRL implements GRPO. Reward functions receive the generated completions plus any dataset columns; this sketch trains a small model on math problems whose dataset has `prompt` and `answer` columns (API as of 2025–26; check the TRL docs for current parameter names):

```python
# grpo_math.py  (pip install trl datasets; a GPU is required)
import re
from datasets import load_dataset
from trl import GRPOConfig, GRPOTrainer

def reward_correct(completions, answer, **kwargs):
    """Verifiable reward: 1.0 if the last number in the completion equals the reference."""
    out = []
    for text, ref in zip(completions, answer):
        nums = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
        out.append(1.0 if nums and nums[-1] == ref else 0.0)
    return out

def reward_format(completions, **kwargs):
    """Small bonus for reasoning inside <think> tags before the answer."""
    return [0.2 if re.search(r"<think>.+</think>", c, re.S) else 0.0 for c in completions]

dataset = load_dataset("json", data_files="math_train.jsonl", split="train")  # {"prompt", "answer"}
trainer = GRPOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    reward_funcs=[reward_correct, reward_format],
    args=GRPOConfig(output_dir="grpo-math", num_generations=8, max_completion_length=512),
    train_dataset=dataset,
)
trainer.train()
```

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Train and Budget a Tiny Reasoner
Extend `grpo_lab.py` into an honest experiment, then (if you have a GPU) repeat the key parts on a real model.
1. Add a third difficulty (`"medium"`: 5 digits) and confirm the learned thinking budget is ordered easy < medium < hard.
2. Implement Dr. GRPO's change (use `r - mean` without dividing by `std`) and compare learning speed and stability over 5 seeds.
3. Add **dynamic sampling**: when a group has zero reward variance, draw a new problem instead of skipping the step. Report how many problems you needed per useful update.
4. Replace majority vote in `solve` with a **verifier-guided best-of-N** (accept the first attempt that a cheap checker validates, for example re-adding the digits from right to left) and compare accuracy per token.
5. Plot accuracy vs average tokens for budgets 0, 2, 4, 8 on hard problems and mark where extra thinking stops paying for itself at your `TOKEN_COST`.
6. On a GPU: run the TRL sketch on a small model with 1,000 grade-school math problems for a few hundred steps; log reward, accuracy and mean completion length, and check whether length grows as in R1-Zero.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Our text-to-SQL assistant, built on a fine-tuned 8B open model, gets about 60% of our internal analytics questions right. Leadership has read about DeepSeek-R1 and wants a 'reasoning version'. Design the training and serving plan. What reward would you use, what could go wrong, and how do you keep latency and cost under control?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **A verifiable reward from execution:** run the generated SQL against a sandboxed replica (or a synthetic database with the same schema) and compare the result set with a reference query's result, order-insensitive where appropriate. Add a small format reward and penalties for invalid SQL or timeouts. Reward result sets, not string match, because many different queries are correct.
2. **The right data and the right difficulty:** build a few thousand question/reference-query pairs from logs and analysts, decontaminate the eval set, and keep problems the current model solves sometimes (pass rate between 0 and 1) so GRPO's group advantages are non-zero.
3. **Recipe: cold start → GRPO → distill or merge:** a short SFT on curated reasoning traces for readable output (possibly written by a stronger teacher), then GRPO with a KL anchor, then rejection-sampled SFT to fold gains back in. They explain why GRPO fits (no critic model, cheap rollouts with vLLM) and consider distilling from a larger reasoning model first, because distillation is often cheaper than RL for small models.
4. **Names the failure modes:** reward hacking (`SELECT` against the wrong table that happens to match, `LIMIT` tricks, exploiting empty result sets), so they use multiple test databases and hidden checks; overthinking, which raises latency; and regressions on non-SQL behavior, so they keep a general eval.
5. **Serving and budget control:** route simple lookups to no/low thinking and complex multi-join questions to higher budgets, cap thinking tokens, stream progress, strip reasoning before parsing the SQL, and measure cost and latency per *correct* answer. They mention parallel sampling plus execution-based verification (run 4 candidates, keep one whose result passes sanity checks) as a test-time alternative that needs no retraining.

---
**Task for the end of the day:** Commit `grpo_lab.py` and your challenge plots to Git. Write one paragraph explaining to a non-ML colleague why a reasoning model sometimes costs 20× more per question and when that is worth it.

We now know that big reasoning models produce long, correct traces, and that SFT on those traces transfers the skill to small models. Tomorrow, in **Day 110**, we scale that idea up: **Synthetic Data Generation at Scale**, including Strong-to-Weak Distillation and chain-of-thought traces (the Orca and R1-distill method)!
