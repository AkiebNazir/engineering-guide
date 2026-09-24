# How Google Scores You — and What "Googleyness" Actually Means

Understand what interviewers write down, because that written feedback is what the hiring committee reads. Google doesn't publish its internal rubric; this is based on Google's public hiring guidance (re:Work, careers pages) and widely reported candidate and interviewer accounts. Treat specifics as "commonly reported," not official.

## 1. The Pipeline

```text
recruiter screen ─► technical phone/video screen(s) ─► onsite loop (virtual or in person)
   │                         │                              │  typically 4-6 interviews:
   │                         │                              │  coding (2-3), system design (1-2 for L5),
   │                         │                              │  Googleyness & Leadership (1)
   ▼                         ▼                              ▼
                     each interviewer writes independent feedback + a rating
                                            │
                                            ▼
               hiring committee (senior engineers who never met you) reads the packet:
               all feedback, resume, sometimes referrals → hire / no hire + level
                                            │
                                            ▼
               team matching (hiring managers) ─► executive/comp review ─► offer
```

- **Independent feedback:** interviewers usually don't compare notes before writing. Each round must stand on its own evidence.
- **Committee, not interviewer, decides.** Feedback that says "strong hire" with thin evidence carries less weight than a detailed "hire." Your job in every round is to **generate specific, quotable evidence**.
- **Team matching** happens after (or in parallel with) committee approval. A candidate can pass committee and still wait for a team match; headcount is a real source of variance unrelated to performance.

## 2. The Four Attributes

| Attribute | What it means | Evidence you produce |
|---|---|---|
| **General cognitive ability (GCA)** | How you break down unfamiliar problems, reason about options, learn and use new information (including hints) | Structured problem decomposition; weighing two approaches; adapting when constraints change; asking clarifying questions that matter |
| **Role-related knowledge (RRK)** | Coding, data structures & algorithms, system design, domain expertise | Correct, efficient, clean code; accurate complexity; defended design trade-offs; depth when pushed |
| **Leadership** | Ownership, driving ambiguous work to outcomes, influencing without authority, mentoring, stepping up *and* stepping back | Stories where **you** scoped, aligned, decided, delivered, and grew others |
| **Googleyness** | Culture-add behaviors (next section) | Stories and in-interview behavior showing collaboration, humility, user focus, comfort with ambiguity, doing the right thing |

Every round produces evidence for more than one attribute. A coding round is mostly RRK and GCA, but how you take a hint is Googleyness evidence, and driving the problem yourself is leadership evidence.

## 3. Googleyness: The Behaviors

Google has described Googleyness with traits like these. Know them well enough to *show* them rather than claim them:

| Trait | Looks like | Anti-pattern |
|---|---|---|
| Comfort with ambiguity | Makes progress with incomplete information; clarifies what matters; states assumptions | Freezes, or demands a full spec before starting |
| Bias to action | Ships an experiment or prototype to learn; doesn't wait for permission when the risk is low | Analysis paralysis; "that wasn't my job" |
| Collaboration | Credits others; seeks input; makes the team better | "I" for everything including other people's work; lone hero stories |
| Humility and intellectual honesty | Admits mistakes and gaps; changes mind with evidence | Defends a wrong position; blames others |
| Openness to feedback | Seeks it; acts on it; can describe how they changed | Only receives feedback they agree with |
| Challenging the status quo | Questions assumptions respectfully with data | Complains without proposing; or never questions anything |
| Putting users first | Frames decisions by user impact | Frames decisions by what was technically interesting |
| Doing the right thing | Raises ethical, privacy, quality, and safety concerns even when inconvenient | Ships something known to harm users because of a deadline |
| Caring about the team | Mentors, includes quieter voices, supports teammates under pressure | Treats teammates as resources |

**In-interview Googleyness** matters as much as stories: how you respond to a hint, how you handle being told your design has a flaw, whether you listen, whether you're pleasant to work with for 45 minutes.

## 4. Leveling: Why L5 Candidates Get L4 Offers (or No Offer)

Every round is also a **leveling signal**. The committee asks "at what level does this evidence sit?"

| Round | Reads as L4 | Reads as L5 |
|---|---|---|
| Coding | Correct optimal solution with some guidance; decent code | Drives the whole round: clarifies, chooses and justifies the approach, writes clean code, **verifies it without prompting**, handles follow-ups and scaling questions |
| System design | Reasonable components once prompted; interviewer steers deep dives | **Drives** requirements, estimates, and deep dives; states trade-offs and commits; raises failure modes before being asked; adapts to changed requirements |
| Behavioral | Good work on a well-defined project within a team | **Scope and ambiguity**: defined the problem, aligned multiple stakeholders/teams, made trade-off decisions, mentored others, measurable business/user impact |

**The three most common causes of downleveling:**
1. **Needing hints in design** — the interviewer had to lead you to the key trade-offs.
2. **Vague or small-scope behavioral stories** — "we built a feature" with no personal decisions, no ambiguity, no cross-team influence, no numbers.
3. **Coding that works but wasn't driven independently** — correct in the end, but the interviewer found the bugs or pointed at the approach.

Map each to its fix: design → `SystemDesign/00_google_l5_playbook.md` and timed mocks; stories → `04_story_bank_worksheet.md`; coding → `CSFundamentals/09_coding_round_execution_deep_dive.md`.

## 5. What the Googleyness & Leadership Round Looks Like

- **Past-behavior questions:** "Tell me about a time you…" — the majority.
- **Hypotheticals:** "What would you do if…" — see `05_hypothetical_questions.md`.
- **Probing follow-ups:** "What was your specific role?", "What would you do differently?", "What did your manager think?", "How did you measure that?", "What happened next?"
- Interviewers typically cover several attributes per story. One strong story can serve 3-4 prompts; you need **coverage**, not dozens of stories.

## 6. Answer Structure: STAR + Lesson

| Part | Share of time | Content |
|---|---|---|
| **Situation + Task** | ~20% | Context in 2-3 sentences: team, scale, the problem, **why it mattered**, what was ambiguous or hard |
| **Action** | ~60% | What **you** did, in first person, with specific decisions and the alternatives you rejected; how you influenced others |
| **Result** | ~15% | Numbers: latency, revenue, cost, incidents, adoption, time saved; plus team/people outcomes |
| **Lesson** | ~5% | What you learned or would do differently, and evidence you applied it later |

**Length:** 2-3 minutes spoken. Longer loses the interviewer; shorter lacks evidence. Leave room for follow-ups.

Blueprints and worked examples: `02_star_method_blueprints.md` and `03_L5_leadership_deep_dive.md`.

## 7. Before Every Practice Session

Name which attribute you're producing evidence for today (e.g., "RRK + GCA: timed coding; Leadership: rewrite the influencing story with numbers"). It keeps practice aimed at what the committee reads.

## Mindset Checks

- [ ] I can explain the four attributes and what evidence each round produces.
- [ ] I can explain why downleveling happens and which part of my preparation addresses each cause.
- [ ] I can list at least six Googleyness behaviors and show each in a story or in how I interview.
- [ ] I understand that team matching and headcount add variance I don't control; my job is to be consistently above the bar in every round.
