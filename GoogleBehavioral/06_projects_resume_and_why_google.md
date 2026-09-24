# Your Projects, Your Resume, and "Why Google?"

Interviewers dig into what you've built — in behavioral rounds, at the start of design rounds, and in team-matching conversations. Vague answers here quietly damage your level: they make every strong story sound borrowed. This file prepares the project deep dive, a resume that survives follow-ups, the 2-minute career summary, "why Google," and your questions for interviewers.

## 1. Project Deep Dive: Prepare Your Top 2-3 Projects

For each project, fill in this sheet and rehearse it until you can do it at a whiteboard without notes.

```text
PROJECT:
ONE-SENTENCE PURPOSE (user problem it solved):

ARCHITECTURE (draw from memory):
  clients → edge → services → data stores → async pipelines → external dependencies
  what each component does, and why it exists

DATA FLOW for the main request path (step by step):

STORAGE CHOICES and why (and what you'd choose today):

REAL NUMBERS:
  traffic (QPS, peak vs average)
  data size and growth
  latency (p50/p99) and availability targets
  team size, timeline, my time on it
  cost (infra $/month if known)
  business/user impact (revenue, conversion, retention, incidents, hours saved)

MY CONTRIBUTION vs THE TEAM'S:
  I designed:
  I decided:
  I led / coordinated:
  I implemented:
  Others did (credit by role):

ALTERNATIVES WE REJECTED and why:

WHAT BROKE (incidents, bottlenecks, bad assumptions) and how we found out:

WHAT I'D DO DIFFERENTLY TODAY:

HARDEST TECHNICAL PROBLEM and how I solved it:
```

### The checks from the prep plan

- [ ] **I can draw the architecture from memory** — components, data flow, storage choices.
- [ ] **I know the real numbers** — traffic, data size, latency, team size, timeline, business impact. If a number is confidential, give an order of magnitude and say so ("tens of thousands of QPS").
- [ ] **I can separate my contribution from the team's** — name what I personally designed, decided, and led.
- [ ] **I can explain the alternatives we rejected and why** — strong evidence of senior judgment.
- [ ] **I know what broke and what I'd do differently today** — shows reflection and growth.

### Expect these questions

- "Walk me through the architecture." (Draw it; start from the user.)
- "Why did you choose X over Y?"
- "What was the bottleneck? How did you find it?"
- "What happens if [component] fails?"
- "How would it change at 10x the traffic?"
- "What was your specific role?"
- "What would you change now?"
- "How did you measure success?"

The design-round habits apply: quantify, state trade-offs, name failure modes. See `SystemDesign/00_google_l5_playbook.md`.

## 2. Resume: Every Line Must Survive 5 Minutes of Follow-Up

**Rule:** remove or reword anything you can't defend in depth. Interviewers pick a line and ask "tell me more."

### Line format
`Action verb + what you did + how (technical specifics) + measurable result + scope`

| Weak | Strong |
|---|---|
| Worked on the payments service | Led redesign of payment retries with idempotency keys and an outbox, cutting duplicate charges from ~0.3% to near zero across 2M transactions/day |
| Improved performance | Reduced checkout p99 latency from 1.2 s to 400 ms by making fraud scoring asynchronous; conversion +2% |
| Used Kubernetes, Kafka, Go | (Put tools inside accomplishment lines, not as a list of buzzwords) |
| Mentored engineers | Mentored 3 engineers; two led their own projects within a year, one promoted |

### Audit your resume

For every line, answer:
- [ ] What exactly did **I** do?
- [ ] What was hard about it?
- [ ] What were the alternatives?
- [ ] How was the number measured?
- [ ] What went wrong?
- [ ] Could I draw the system involved?

Also: every technology listed is fair game for a deep question. Keep the resume to what shows L5 scope: ownership, ambiguity, cross-team work, impact.

## 3. The 2-Minute Career Summary ("Tell me about yourself")

Used by recruiters and often at the start of rounds. Structure:

1. **Now (30 s):** current role, team, scope, what you own.
2. **Arc (45 s):** 2-3 prior steps that show a thread (growing scope, a domain, a type of problem) — not a full chronology.
3. **Highlight (30 s):** one project with impact and a number.
4. **Next (15 s):** what you want to do next, which leads naturally to this role.

Template:
> "I'm a [role] at [company], where I lead [area] — [scope: team size, systems, users]. Before that I [prior step] and [prior step], and the common thread has been [thread]. Recently I [highlight project] which [impact with number]. I'm now looking to [what you want], which is why this role on [area] interests me."

Rehearse to exactly ~2 minutes. Don't recite the resume.

## 4. "Why Google?"

A real answer is specific to you, not a compliment to Google. Combine three things:

| Ingredient | Example angle (use your own) |
|---|---|
| **The work** | A product, system, or problem space at Google you care about and why (e.g., reliability at planetary scale, a specific product area, research-to-production pipelines) |
| **How Google works** | Things that match how you like to work: design docs and review culture, monorepo and shared infrastructure, SRE practices, data-driven decisions, openness of internal knowledge |
| **Your growth** | What you want to learn or do next that Google's scale or teams make possible |

Avoid: perks, prestige, "it's the best company," anything you couldn't expand for 2 minutes. Tie it back to something concrete in your experience ("At my company I built X at a scale of Y; I want to work on the same class of problems where…").

Prepare **"Why this team / area?"** for team matching too.

## 5. Questions to Ask Your Interviewers

Always have 3-4 real questions. They signal interest and judgment, and the answers help you choose a team.

**About the work**
- "What does a successful first six months look like for someone in this role?"
- "What's the hardest technical problem your team is working on right now?"
- "How are priorities decided between product requests and technical debt?"

**About engineering practice**
- "How do design reviews work on your team? Can you tell me about a recent design that changed because of review?"
- "How does the team handle on-call and incidents?"

**About growth and culture**
- "How do engineers here grow into larger scope, like from L5 to L6?"
- "What's something you'd change about how your team works?"

Avoid questions answered on the careers page, and save compensation for the recruiter.

## 6. Logistics and Final Week

- Confirm interview format (virtual doc vs in person whiteboard); practice in that medium.
- For virtual rounds: stable internet, a quiet room, a simple editor or shared doc tested in advance, water.
- The night before: light review of your story bank and project sheets only. Sleep.
- During the loop: each round is independent — a rough round doesn't mean a failed loop; reset between rounds.
- After: note questions and your answers while fresh (useful if you interview again).

## Checklist

- [ ] Project sheets complete for my top 2-3 projects, rehearsed at a whiteboard.
- [ ] Every resume line survives 5 minutes of follow-ups.
- [ ] 2-minute career summary timed and rehearsed.
- [ ] A specific "why Google" and "why this team."
- [ ] 3-4 questions ready for each interviewer.
