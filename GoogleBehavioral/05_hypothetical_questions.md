# Hypothetical Questions — "What Would You Do If…"

Google behavioral rounds mix past-behavior questions with **hypotheticals**. There's no story to retell, so interviewers see your judgment directly: how you gather information, weigh stakeholders, balance speed with care, and treat people.

## A Framework That Works for Any Hypothetical

1. **Clarify the situation** (briefly): stakes, timeline, who's involved, what you know vs assume. "Before I act, I'd want to know whether…"
2. **Gather information and perspectives** before judging. Assume good intent first.
3. **Identify options** (usually 2-3) and the trade-offs of each, especially user impact and reversibility.
4. **Decide and act**, starting with the least escalated effective step.
5. **Communicate** transparently to the right people at the right time.
6. **Escalate** only if earlier steps fail or the stakes demand it, and say how.
7. **Follow through and learn:** what you'd put in place so it doesn't recur.

Where possible, **anchor to a real experience**: "I haven't faced exactly this, but something similar happened when…" That converts a hypothetical into evidence.

---

## The Three From the Prep Plan

### 1. Your team strongly disagrees with a product decision from leadership

**What they're probing:** respect for decisions, courage to disagree, data-driven influence, disagree-and-commit.

**Strong answer outline:**
- Understand the decision first: talk to the decision-maker or PM to learn the *why*, the constraints, and what success looks like. Leadership often has context the team doesn't (commitments, market data, legal).
- Separate the team's concern into **facts and risks** (user impact, technical risk, cost) vs preferences.
- Gather evidence: data from experiments, user research, support tickets, a quick prototype, an estimate of cost or risk.
- Raise it through the right channel — a concise written doc or meeting with leadership — with options, not just objections ("launch as planned with these mitigations", "A/B test first", "phase the rollout").
- **Represent the team honestly** without making it "us vs them."
- If the decision stands: **commit fully**, explain the reasoning to the team so they can commit too, and set up metrics to check the outcome, with an agreed point to revisit.
- **Exception:** if the concern is ethical, legal, privacy, or safety, escalate further and don't simply commit.

**Anti-patterns:** complying silently; building it half-heartedly; venting to the team and undermining leadership; escalating over your manager first.

### 2. A teammate consistently misses commitments

**What they're probing:** empathy, directness, supporting people, protecting the team's delivery.

**Strong answer outline:**
- Check your own understanding: are the commitments clear, realistic, and actually agreed? Is there a pattern or a few incidents?
- **Private, empathetic conversation first:** describe specific instances without judgment, ask what's going on. Causes vary — unclear expectations, overload from other work, skills gap, personal circumstances, low motivation.
- **Support based on the cause:** clarify scope, break work into smaller milestones with check-ins, pair on the hard parts, help them push back on other demands, share context.
- **Protect the project meanwhile:** adjust plans or dependencies transparently so the team isn't blindsided.
- **Escalate** to the manager if it continues or if it's a performance/personal matter beyond a peer's role — framed as getting them support, not blame.
- **Follow through:** check in again; recognize improvement.

**Anti-patterns:** going to the manager first; complaining to others; silently doing their work for them indefinitely.

### 3. You find a serious bug in a colleague's code the day before launch

**What they're probing:** user focus, doing the right thing, transparency, collaboration under pressure.

**Strong answer outline:**
- **Confirm and assess quickly:** reproduce it; determine severity — data loss, security/privacy, money, how many users, whether it's behind a flag.
- **Tell the colleague immediately and privately**, as a teammate ("I think I found something in X; can we look together?"), not as a gotcha. They know the code best.
- **Bring options to the launch owner** (TL/PM) quickly, with the facts: fix now and re-test, launch with the feature flag off or at reduced scope, delay, or launch with a known low-risk issue and a fix scheduled.
- **Decide based on user impact and reversibility:** a severe bug (data loss, security) means don't ship that part; a cosmetic bug may ship with a follow-up.
- **Communicate transparently** to stakeholders about the decision and the risk.
- **Afterwards:** a blameless look at why tests and review missed it; add the test; improve the process.

**Anti-patterns:** staying quiet to avoid conflict; quietly fixing it yourself without telling anyone; announcing it publicly to shame the colleague; launching a known severe bug to hit the date.

---

## More Hypotheticals Worth Rehearsing

For each, apply the framework and write a 5-bullet outline.

| Hypothetical | Key tension | Strong move |
|---|---|---|
| You're asked to build something you believe harms users (e.g., dark patterns, excessive data collection) | Business goal vs user trust/ethics | Raise concerns with data and principles; propose alternatives that meet the goal; escalate through ethics/privacy review if needed |
| Your project is cancelled halfway through | Sunk cost, team morale | Understand why; capture learnings and reusable parts; help the team transition; be honest about disappointment without cynicism |
| You join a team with a legacy system everyone hates | Rewrite vs incremental improvement | Learn why it's the way it is; measure the real pain; propose incremental strangler-fig migration with milestones over a big-bang rewrite |
| Two senior engineers on your project are deadlocked on a design | Progress vs harmony | Get both options written down with criteria; timebox; prototype or benchmark the crux; agree on a decider; document the decision |
| You realize your estimate was badly wrong midway | Transparency vs embarrassment | Tell stakeholders early with a revised plan and options (cut scope, add people, move date); explain what you learned about estimating |
| A customer-facing outage happens while you're on call and you don't know the system | Calm, mitigation, communication | Declare the incident, follow runbooks, page the owners, mitigate (rollback/drain), communicate on a cadence; learn and improve runbooks after |
| Your manager asks you to cut corners on testing to hit a date | Speed vs quality | Quantify the risk; propose options (scope cut, flag-gated launch, test the risky paths only); agree on explicit risk acceptance and a follow-up |
| A new teammate is struggling and seems afraid to ask questions | Inclusion, psychological safety | Reach out privately; normalize questions; set up regular 1:1 or pairing; model asking questions publicly yourself |
| You get conflicting priorities from two stakeholders | Alignment | Make the conflict visible; bring both together (or to the shared manager) with the trade-offs; get an explicit decision rather than choosing silently |
| You discover a colleague took credit for your work | Fairness vs relationship | Talk to them directly first; assume misunderstanding; make contributions visible going forward (design docs, updates); involve the manager if it persists |
| A metric you own improves dramatically overnight | Skepticism, data integrity | Verify before celebrating: instrumentation changes, bots, logging bugs, experiment misconfiguration |
| You're given a project with no PM, no spec, and a one-sentence goal | Ambiguity, ownership | Talk to users/stakeholders, define success metrics, write a short design doc with milestones, validate early with a prototype |

## Practice

- Pick three hypotheticals; answer each out loud in ~2 minutes using the framework.
- For each, add one sentence tying it to a real experience.
- Ask a mock partner to change a detail mid-answer ("the colleague is your manager"; "the launch is contractual") and adapt.
