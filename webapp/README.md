# Ultimate Engineering Guide

A local web app for the `PyDSA/` + `GoDSA/` curriculum. Reads your problem files
straight off disk, runs your code in **both languages for real**, and saves
everything to `webapp/data/progress.json`.

```bash
./studio                 # http://127.0.0.1:8420, opens your browser
./studio 9000            # different port
```

No `pip install`, no `npm install`, no build step — the server is Python stdlib only.

---

## What it does

| | |
|---|---|
| **Runs your code** | Python via your `.venv`, Go via `go run`. Real subprocesses, real output, 15s/40s timeouts so an infinite loop can't hang the app. |
| **Saves everything** | Drafts, status, notes, timer, streak — written to disk on every change and on tab close. Close the browser, kill the server, reboot: it's all still there. |
| **Two languages per problem** | Toggle Python/Go; each keeps its own independent draft. |
| **Timer with the hint ladder** | Counts up per problem. Warns at **25 min** (take one hint) and **40 min** (open the solution) — the ladder from `master_dsa_plan.md` §0. |
| **Spaced repetition** | Marking a problem solved schedules a cold re-solve at D+1 → D+3 → D+10 → D+30. The Review queue shows what's due. |
| **Pattern journal** | A Notes tab per problem for the trigger→technique line. |
| **Pattern pages** | `#/t/<topic>` — one pattern, its progress ring, difficulty mix and every problem in it as a scannable list with status, review-due and time-on-problem. Filter by status or difficulty, reorder by unsolved-first or easiest-first, step to the previous/next pattern. Reached from a card or cell on the DSA home, from the topic name in the sidebar, or from the breadcrumb above an open problem. |
| **Topic guides** | Every DSA topic has a deep-dive guide in **both languages** — Python (`#/dsa-guide/<topic>`) and Go (`#/dsa-guide-go/<topic>`) — opened from the *Read the topic guide* **Python / Golang** buttons on the pattern page. Each is a full reader page (contents rail, section checks, highlights, focus mode, prev/next guide, zoomable diagrams), with a language switch in its header. |
| **Visualize tab** | A step-by-step player per topic: 50 animated algorithms across all 28 DSA topics, with the matching Python line highlighted, scrubbing, playback speed, and your own input. |
| **Progress** | Per-topic rings, difficulty breakdown, practice streak, total time. |

## The sidebar

Deliberately flat: **Dashboard · Review queue**, the DSA filter chips, then one
row per module with its progress.

```
Dashboard
Review queue                      3
[ All  Easy  Med  Hard ]
[ Any  Todo  Solved  ★ ]
  DSA                        128/344
  System Design                4/71
  Software Design              0/32
  Go Engineering · Py Engineering · AI Roadmap · AI Library Guides
  Agentic AI · CS Fundamentals · Google Behavioral
```

Topics and problems are not in the rail — they live on the pages, where there is
room for them: **DSA → pattern page (`#/t/…`) → problem**, and each module's
landing page → its cards.

Type two or more characters in the search box and the module list becomes a flat
**result list across the whole library** — DSA problems and every module's pages
together, each row labelled with where it came from. The difficulty and status
chips narrow the DSA half of those results.

## Learning modules

System Design, Software Design, Go Engineering, Py Engineering, <abbr title="Artificial Intelligence">AI</abbr> Roadmap, <abbr title="Artificial Intelligence">AI</abbr> Library
Guides, Agentic <abbr title="Artificial Intelligence">AI</abbr>, CS Fundamentals and Google Behavioral each get:

| | |
|---|---|
| **Own colour** | The whole app re-tints when you enter a module (indigo, cyan, green, violet, coral, pink). |
| **Sidebar row** | One row with its own progress; the contents are on its landing page, not in the rail. |
| **Category rail** | A module with more than one group gets a sticky chip rail above the cards — every group with its done count, click to jump, and it marks the group you are scrolled into. |
| **Landing page** | A drawing of the subject that shows your progress (the roadmap path is drawn as far as you've read), a Continue button, and grouped cards. |
| **Reader** | On-this-page rail with scroll-spy, "Got it" check per section, highlights (select text), callout cards for 💡/⚠️/**Analogy:**/**Example:** blocks, highlighted code with copy, zoomable diagrams (architecture and flow diagrams are ` ```arch ` blocks drawn in AWS reference style; see [`ARCH_DIAGRAMS.md`](ARCH_DIAGRAMS.md)), reading position restored. |
| **Page themes** | `Aa` menu: App / Sepia / Night, text size, line length, sans or serif. |
| **Practice problems** | System design problems hide the reference design until you choose to open it. |

**Software Design** is one ordered path, numbered by step: a Start-here page
(`SoftwareDesign/README.md`), 14 chapters in four parts, then 17 LLD problems in
recommended practice order. The order lives in `server.py` (`SWD_CHAPTER_PARTS`,
`SWD_LLD_SETS`). LLD problems open in the code workspace: the brief is
`lld/NNN_slug_question.py`, **Run** executes that file with your code swapped in (its
tests are built in; only `ALL PASSED` counts as solved), and the Solution tab renders
`NNN_slug_solution.py`.

**Solutions are hidden until you press "Reveal solution"**: System Design reference designs and
DSA solutions alike (`static/solution-gate.js`). Leaving the problem hides them again. A revealed
DSA solution opens with a "Watch it run" animation (the exact problem where one exists, otherwise
the topic's pattern). System Design problems can carry animated request flows
(`static/sd-flow.js`, e.g. the URL shortener's create / redirect / miss / 404 / outage walkthrough).

Reader keys: `J`/`K` next/previous section · `C` check section · `[`/`]` previous/next page · `F` focus mode · `Esc` close.

Reading state lives in `progress.json` under `docs`.

## Layout

```
webapp/
  server.py            stdlib HTTP server: files, execution, persistence
  static/
    index.html         structure
    styles.css         design system (dark + light, all tokenised)
                       — editor is VS Code Dark Modern / Light Modern
    app.js             router, editor, timer, review scheduling
    dsa-home.js        DSA landing page (#/dsa)
    dsa-topic.js/.css  one pattern and its problems (#/t/<topic>)
    reader.js          learning modules: data, landing pages, reader
    reader.css         module colours, reader layout, page themes, callouts
  data/
    progress.json      ← your state. Back this up; delete it to reset.
```

The problem files remain the single source of truth. Edit a `.py`/`.go` file on
disk and it shows up in the app on reload — the app never writes to them, only
to `progress.json`.

## Keyboard

| Key | Action |
|---|---|
| `⌘/Ctrl + ⏎` | Run code |
| `⌘/Ctrl + B` | Toggle sidebar |
| `⌘/Ctrl + ⇧ + T` | Start / pause timer |
| `/` | Focus search |
| `1` `2` `3` `4` `5` | Question · Solution · Visualize · Guide · Notes |
| `Esc` | Clear search |

In the editor (VS Code bindings):

| Key | Action |
|---|---|
| `⌘/Ctrl + /` | Toggle comment |
| `⌘/Ctrl + F` | Find · `⌘G` / `⌃G` next |
| `⌥G` / `⌃G` | Jump to line |
| `⇥` / `⇧⇥` | Indent / outdent selection |
| `⌘/Ctrl + S` | Save draft now |

## Status marks

`○` todo · `◐` attempting · `●` solved · `★` mastered

Only `★` counts toward interview readiness — it means cleared cold through all
four review intervals. Same bar as `master_dsa_plan.md`.

## Notes

- **Binds to `127.0.0.1` only.** It executes code you type, on your machine, as
  you — the same trust model as a Jupyter notebook. Don't expose it to a network.
- **Go run takes ~0.8s** on first compile per snippet; that's the toolchain, not
  the app. Python is ~15ms.
- **Offline:** the code editor and markdown renderer load from cdnjs. Without a
  connection the app still works — the editor falls back to a plain textarea.
- **Theme:** the toggle cycles **system → light → dark**. `system` follows the
  OS and flips live. The choice is mirrored to `localStorage` so a reload paints
  the right ground before first paint — no flash. The editor is a port of
  VS Code's own default themes; every syntax colour clears 4.5:1 against its
  ground in both modes, so nothing is a squint in either.
- **Reset progress:** delete `webapp/data/progress.json`.
