# Level Calibration: Telling the Same Story at L4, L5 and L6

Every behavioral answer is also a **leveling signal**. The hiring committee doesn't just ask "hire or no hire?"; it asks "at what level does this evidence sit?" Two candidates can tell the same project and get different levels, because one describes executing a well-defined task and the other describes defining the problem, aligning people, and changing how the organization works.

This file gives you a systematic way to see what level a story reads at, and to tell it at the level it truly reached. File [How Google Scores You](01_how_google_scores_and_googleyness.md) §4 has the round-by-round L4 vs L5 table; this file goes deeper on the behavioral round and adds L6.

> **What this is not:** a way to inflate stories. Interviewers spend five minutes on follow-ups precisely to test whether the scope you claimed is real. The goal is to stop *underselling* work you really did (very common) and to recognize when you need a bigger story.

---

## 1. The Ladder in Plain Terms

Google doesn't publish its internal leveling guide. The descriptions below come from Google's public careers information and widely reported accounts; treat them as "commonly reported," and the experience ranges as rough, since plenty of people sit outside them.

| Level | Common title | Rough experience (approximate) | One-line expectation |
|---|---|---|---|
| L3 | Software Engineer II | New grad to ~2 years | Delivers well-scoped tasks with guidance |
| L4 | Software Engineer III | ~2-5 years | Owns features and components independently within a team |
| L5 | Senior Software Engineer | ~5-8+ years | Owns ambiguous projects end to end; leads across teams; grows others |
| L6 | Staff Software Engineer | ~8+ years | Sets technical direction for an area spanning several teams; solves problems nobody assigned |
| L7+ | Senior Staff, Principal, … | Varies widely | Org- or company-wide technical direction |

L5 is widely described as the "career level": engineers aren't expected to go beyond it, and many excellent engineers stay there. Most external hires interview for L3-L5. L6+ loops typically weigh system design and leadership more heavily, and the bar for behavioral scope rises sharply.

## 2. The Four Dimensions That Change

Every story can be placed on four dimensions. The same four words show up in how interviewers write feedback, so use them in your own self-assessment.

| Dimension | Question the committee asks | L4 | L5 | L6 |
|---|---|---|---|---|
| **Scope** | How big was the thing you were responsible for? | A feature or component within one team's project | A project spanning your team plus 2-4 adjacent teams, or a whole service | A technical area or problem spanning many teams or an org, often over multiple projects |
| **Ownership** | Which parts of the outcome were yours? | Your component's design, code, tests and rollout; the project plan was someone else's | The whole project: problem definition, design, plan, people coordination, launch, results | The direction: *which* projects should exist, how they fit together, and whether the org is solving the right problem |
| **Ambiguity** | How much was defined for you? | The problem and solution shape were given; you resolved the technical unknowns | The problem was given ("checkout is slow"); you defined the solution, success metrics and plan | The problem itself was unclear or unnoticed; you identified and framed it |
| **Impact** | What changed, and for whom, for how long? | Your feature shipped and worked; measurable improvement to one system | A business or user metric moved; other teams benefited; a pattern was reused | The org works differently: a platform, standard or strategy many teams now use; durable beyond you |

Two more dimensions come along with those four:

| Dimension | L4 | L5 | L6 |
|---|---|---|---|
| **Influence** | Persuades teammates with evidence | Aligns other teams and senior engineers without authority | Aligns directors and staff engineers; changes defaults so teams opt in on their own |
| **Multiplier effect** | Helps onboard new hires | Grows L3/L4s into project leads | Grows future tech leads; builds practices that run without them |
| **Time horizon** | Weeks to a quarter | A quarter to a year | A year or more; plans for multi-year consequences |

## 3. The Language Ladder

Committee members read written feedback, and interviewers often quote you. The verbs you use decide what they can quote. Don't use verbs you can't back up; do stop using verbs that shrink real work.

| | L4 language | L5 language | L6 language |
|---|---|---|---|
| **Problem** | "I was asked to…", "my lead assigned me…" | "I was given a goal of X and had to work out what that meant" | "I noticed that…", "nobody owned…", "I made the case that we should…" |
| **Decision** | "I implemented the approach we chose" / "I chose between two libraries for my component" | "I evaluated three designs against these criteria and decided…" | "I set the direction that N teams would converge on…", "I decided what we would *not* build" |
| **People** | "I worked with my teammate on…" | "I aligned the PM, the platform team and security…", "I mentored X to own…" | "I got two directors to agree…", "I grew three engineers into TLs for the workstreams" |
| **Result** | "My feature cut latency by 30%" | "p99 dropped 400 ms, conversion rose 2%, two other teams adopted the pattern" | "It became the default for the org; 14 services migrated; the incident class disappeared" |
| **Lesson** | "I learned the library's edge cases" | "I learned to validate the requirement with users first" | "I learned how to sequence org-wide change so teams can absorb it" |

**Phrases that quietly downlevel you:**
- "We decided…" (when you decided). Say "I proposed…, and the team agreed."
- "I helped with…" (when you led it). "Helped" makes the interviewer assume a small role.
- "My manager asked me to…" as the start of every story. Fine sometimes; if it's always, you look like you only execute assignments.
- "It went well." Without a number, nobody can write it down.

**Phrases that overclaim (and get caught on follow-ups):**
- "I led the migration" when you migrated your own team's service in a project someone else ran.
- "I set the strategy" when you wrote one section of a doc.
- "I mentored the team" with no named person and no before/after.

## 4. The Same Story at Three Levels

Below is one project, a slow checkout page, told honestly by three different engineers at three different levels. The facts differ because **their roles really differed**; the point is to see what each role sounds like.

### The L4 version: owning a component

*   **S:** Our checkout page's p99 latency had grown to 2.1 seconds. My tech lead had profiled it and found that the order-summary API made one database query per cart item, an N+1 query pattern.
*   **T:** My TL assigned me to fix the order-summary service, with a target of cutting its latency in half within the sprint.
*   **A:** I reproduced the problem with a load test against a staging copy of production data. I compared two fixes: batching the queries into a single `WHERE id IN (...)` query, or adding a cache in front of the product table. I chose batching, because product prices change often and a cache would have needed an invalidation story we didn't have. I rewrote the data-access layer, added a regression test that asserted the query count per request, and rolled it out behind a flag at 1%, 10%, then 100% while watching error rates.
*   **R:** The order-summary API's p99 dropped from 800 ms to 120 ms, and overall checkout p99 fell by about 30%. The query-count test caught a similar regression two months later. I learned to guard performance fixes with a test, or they decay.

**What makes it L4:** the problem was found and framed by someone else; the scope was one service; the decision was local (batching vs cache) but reasoned well; the impact was real and measured. This is a **strong L4 story**. For an L5 loop it is too narrow on its own.

### The L5 version: owning the project

*   **S:** Checkout p99 latency had grown to 2.1 seconds, and the product director told me conversion was dropping on mobile. The request was one sentence: "Make checkout fast."
*   **T:** I owned the project end to end: find the actual causes, decide what to fix, align the three teams whose services checkout called, and show that conversion recovered.
*   **A:** I didn't start with a fix. I added distributed tracing across the checkout path and found three causes: an N+1 query in order-summary (~35% of latency), a synchronous call to a fraud-scoring vendor (~40%), and a render-blocking script (~15%). I defined the success metric with the PM: p99 under 1 second and mobile conversion back to its previous level. I split the work into three milestones and handed the N+1 fix to an L4 engineer on my team, reviewing his design. The fraud call was the hard part, because the payments team owned it and was nervous about fraud risk. I met their TL and our risk analyst, proposed scoring asynchronously for low-value carts, holding orders for review when the score came back high, and showed from historical data that the expected fraud loss increase was small compared with the revenue we were losing to latency. They agreed to a two-week A/B test with a hard fraud-rate guardrail.
*   **R:** p99 dropped from 2.1 s to 850 ms; mobile conversion recovered by 2.3% in the experiment; fraud loss stayed within the guardrail. The async-scoring pattern was later adopted by the subscriptions team. The L4 engineer who did the N+1 fix led the next performance project. I learned that the requested fix is rarely the one with the most impact; measure first.

**What changed from L4:** the engineer **defined the problem** from a one-line goal (ambiguity), **owned the whole outcome** including a business metric (ownership, impact), **influenced another team** with data and a guardrail (influence), and **delegated** a piece to grow someone (multiplier). The N+1 fix is now one line, not the whole story.

### The L6 version: owning the direction

*   **S:** While reviewing performance problems across the commerce org, I noticed checkout was not a one-off: in the past year, 5 teams had each run their own latency project, and each found the same root causes. Synchronous calls to slow dependencies and missing performance budgets kept creeping back. No one owned latency across the org.
*   **T:** Nobody asked me to fix this. I decided the org needed a shared approach to latency, not a sixth one-off project, and took on making the case, designing it, and getting the teams to adopt it.
*   **A:** I wrote a strategy doc that quantified the problem across all five past projects: roughly 18 engineer-months spent re-solving the same causes, and regressions within 2 quarters in 4 of 5 cases. I proposed three pieces: a per-page latency budget enforced in CI, a standard async-with-guardrail pattern for risk-scoring calls, and org-wide tracing on by default in the service framework. I deliberately left out a central "performance team," because it would have made latency someone else's problem. I reviewed the doc with two directors and three other staff engineers, and changed the budget enforcement from blocking to warning for the first quarter after the mobile director argued a hard block would stall their launches. I recruited one L5 from each of three teams as workstream leads, mentoring them through their designs, and ran the checkout team's migration as the first proof point.
*   **R:** Within three quarters, 12 of 14 customer-facing services were on the latency budget. p99 for the top five user journeys improved between 25% and 55%, and in the following year no team needed a dedicated latency project. Two of the three workstream leads were later promoted, one to staff. I learned that an org-wide change sticks when it's built into the defaults (the framework, the CI) rather than into a process people have to remember.

**What changed from L5:** the engineer **found a problem nobody had assigned** (ambiguity at the problem level), set a **direction across many teams** rather than running one project (scope), **negotiated with directors** and made a real concession (influence), **built leaders** for the workstreams (multiplier), and the impact is **durable and structural** (impact, time horizon).

### Side-by-side

| | L4 | L5 | L6 |
|---|---|---|---|
| Who found the problem | Tech lead | Director gave a goal; engineer found causes | Engineer noticed a pattern across teams |
| Unit of work | One service fix | One cross-team project | A strategy and several projects |
| Hardest person to convince | None (local decision) | Payments TL and risk analyst | Two directors and peer staff engineers |
| Numbers | Service p99 800 → 120 ms | Page p99 2.1 → 0.85 s, conversion +2.3% | 12/14 services on budgets; no repeat projects |
| People outcome | — | L4 led next project | Two workstream leads promoted |
| Lasting change | A regression test | A reusable pattern | Org defaults (framework and CI) |

## 5. A Second Example, Condensed: The Production Incident

The incident story (blueprint 11 in [The STAR Method: Google Blueprints](02_star_method_blueprints.md)) changes shape in the same way:

| | L4 | L5 | L6 |
|---|---|---|---|
| **Role in the incident** | Responder: found the bad config in logs and executed the rollback under the IC's direction | Incident commander: coordinated responders, ran comms cadence, made the rollback call | May not be in the incident at all; acts on the *pattern* across incidents |
| **Postmortem** | Wrote the timeline; added an alert for the failure | Led the blameless postmortem; drove the config-canary fix across the teams who push configs | Reviewed a year of postmortems, found config changes caused ~a third of outages, and led an org-wide change so configs ship through the same progressive rollout as code |
| **Result language** | "Our team got an alert that fires 10 minutes earlier" | "Config canaries caught two bad pushes before they hit more than 1% of traffic" | "Config-caused outages across the org fell by more than half in a year" |

## 6. How Interviewers Test Your Level

Follow-up questions are where claimed scope gets verified. Expect these, and know what each one is checking:

| Follow-up | What it tests | L5+ answer contains |
|---|---|---|
| "Who decided the scope?" / "Where did the requirements come from?" | Ambiguity | You, from a goal: "The ask was X; I turned it into Y after talking to Z" |
| "What would have happened if you'd left halfway?" | Ownership | "The project would have stalled; I held the plan and the cross-team relationships" |
| "Who disagreed, and how did you resolve it?" | Influence | A named role on another team, their valid concern, and what you changed |
| "What did you personally do vs the team?" | Ownership honesty | Clear I/we split, with credit given to others |
| "How did you measure success, and who agreed on that measure?" | Impact | A metric defined up front with stakeholders |
| "What happened six months later?" | Durability | Adoption, reuse, no regressions, people outcomes |
| "What would you do differently?" | Judgment | A real mistake or trade-off in hindsight, not a disguised boast |

## 7. Reshaping Your Own Stories

**Step 1: place each story honestly.** For each story in your bank ([Your Story Bank](04_story_bank_worksheet.md)), score the four dimensions from §2 as L4, L5 or L6. A story reads at the level of its *typical* dimension, not its best one; one L6 dimension with three L4 ones reads L4.

**Step 2: stop underselling.** Most candidates tell their stories one level lower than they happened, because they narrate the technical work and skip the rest. Look for parts you did but didn't mention:
- Did you turn a vague request into a concrete plan? That's ambiguity. Say it.
- Did you talk to another team, PM, security or legal? That's influence. Say who and what they wanted.
- Did you hand part of the work to someone and review it? That's delegation and mentoring. Say it.
- Did the result change a business or user metric, or get reused? That's impact. Find the number.

**Step 3: zoom out the frame, zoom in on decisions.** Spend less time on the code and more on the moments where you chose: what to build, what not to build, who to involve, what to trade. At L5+, the implementation is one sentence.

**Step 4: if a story truly sits a level below your target, replace it.** No rewording turns a well-specified ticket into an L5 story. Look for a bigger story in your raw material (step 1 of the worksheet). If you don't have enough target-level stories, that is useful information: an L4 offer with a fast path to L5 may be the right outcome, and it's better than failing an L5 loop with inflated stories.

**Step 5: re-test with follow-ups.** For each reshaped story, run the §6 questions. If any answer is "well, actually my lead did that," move the story back down.

## 8. Notes for Specific Situations

- **Interviewing for L5 from a small company:** scope is relative. Leading the only backend migration at a 30-person startup, aligning the CTO, mobile and sales, can be strong L5 evidence. Explain the scale clearly (team size, users, revenue at stake) so the committee can calibrate.
- **Interviewing for L5 from a big company as an L4:** your best stories are probably the ones where you acted beyond your role. Lead with those, and be explicit about what you owned versus what your lead owned.
- **Interviewing for L6:** expect every story to be probed for "was this your idea?" and "how many teams?" Have at least two stories where you identified the problem yourself, and one where you changed direction after strong pushback from someone senior. Staff engineers are often described through archetypes (tech lead, architect, solver, right hand, per Will Larson's *Staff Engineer*); know which one your stories show.
- **Interviewing below your current level:** don't shrink your stories. Tell them at the level they happened; the committee levels on evidence, and extra scope doesn't hurt.

## Calibration Checklist

- [ ] I've scored every story in my bank on scope, ownership, ambiguity and impact.
- [ ] At least 6 of my stories read at my target level on their typical dimension.
- [ ] I've rewritten my strongest story at my target level and one level above, and I can see which one is honest.
- [ ] No story uses "we" where I mean "I", or "helped" where I led.
- [ ] Every story survives the seven follow-ups in §6 without "actually, my lead did that."
- [ ] For L6 targets: at least two stories where I found the problem myself, and one where the change outlived my involvement.
