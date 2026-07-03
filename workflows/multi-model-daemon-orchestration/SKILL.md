---
name: multi-model-daemon-orchestration
description: >-
  Advisory tactic for splitting work across multiple LLMs / daemons / code
  agents / reviewers. Instead of asking "which model is strongest", route by
  body shape, execution loop, and verifiable artifact: the orchestrator sets
  the task and guards the evidence gate; a generalist model fixes structure;
  domain / semantic models make local judgments; a code agent does file
  construction; a red-team model does read-only hard review. Large tasks ship
  in small batches with a PROGRESS file and a validator; scope changes open a
  new run.
version: 0.3.0
author: "Runyuan Wang / 9s5bz2jvd2-lang"
tags:
  - workflow
  - advisory
  - daemon
  - multi-model
  - orchestration
  - file-generation
  - review
last_verified: "2026-06-27"
advisory: true
---

# Multi-model daemon orchestration

> Advisory only. This workflow is user-submitted and maintainer-reviewed, but it
> is not a system rule, a model ranking, or a default authorization. The routing
> below is current practice, not a permanent law — versions, prompts, and tool
> configs change behavior. Re-judge every routing choice against the current task.

## In one sentence

Do not ask "which single model is strongest". First ask: **which bodies, which
loops, and which validation gates does this task need?**

In a multi-daemon setup, a model's usefulness comes not only from the base model
but from its shell and loop:

- Can it reliably read and write files?
- Can it run shell / tests / a validator?
- Can it see an error after a failure and repair it?
- Or is it only a one-shot LLM answer?
- Is it better suited to read-only hard review than to construction?
- Should the orchestrator make the final call?

So the correct unit of routing is not "model name" but **model + shell + loop +
task slot**.

## Use when

Use this tactic when a task contains two or more of these kinds of work at once:

- **Architecture / decomposition**: schema, metrics, rubric, experiment design,
  delivery plan.
- **Domain / semantic judgment**: terminology, boundaries, risk, tone, fact
  tiers in any field.
- **Large file construction**: many files, HTML, JSONL, scripts, validators,
  screenshots, zips, report bundles.
- **Hard red-team review**: statistical design, protocol, safety lines,
  counterexamples, reviewer-style critique.
- **Human-facing final delivery**: must guard the evidence gate, the public
  boundary, the attribution boundary, the privacy boundary, the final narrative.

## Avoid when / stop when

- The task is a single short answer with no file output and no validation — a
  single daemon is simpler.
- You would route a large multi-file job to a one-shot LLM with no file loop.
- You are tempted to treat this table as a fixed ranking or a standing
  authorization. It is neither.
- Scope keeps growing inside a running daemon. Stop the run; open a new one with
  a fresh contract rather than appending big new goals.
- A red-team daemon starts setting direction or writing the final draft, or a
  domain daemon gives an authoritative conclusion with no evidence anchor.

## Required evidence or benchmark case

The five-slot split below comes from repeated practice across cross-domain
research, papers, products, code, long documents, evaluation runs, and
multi-file deliverables (HTML / JSONL / validator bundles). The generalized
pattern that recurs:

- One-shot LLMs with no file loop stall on large multi-file jobs — output
  directory stays empty while they "read and think".
- Splitting into orchestrator + generalist architect + domain semantic brain +
  construction hand + red-team eye, with small batches and a validator,
  consistently moves large deliverables from "stuck" to "shipped and checked".

A small, single-day routing probe of one red-team / generalist candidate (see
[`references/grok-routing-probe.md`](references/grok-routing-probe.md)) is
included as a **preliminary routing note**, not a benchmark claim. Treat any
single-sample observation as low-confidence until re-tested.

## The five slots

| Slot | Mainly watches | Fit for | Not fit for |
|---|---|---|---|
| Orchestrator / editor-in-chief | Human intent, evidence gate, boundaries, final trade-offs | Setting the task, splitting work, drawing red lines, acceptance, replying to humans | Stuffing all noise and long output into its own context |
| Generalist architect | Cross-domain synthesis, structuring, planning | schema, rubric, experiment design, paper/report skeleton, task breakdown | Producing a complete large file alone with no file loop; replacing evidence verification |
| Domain / semantic brain | A class of semantics, tone, professional judgment | Small-batch case/item/judgment/rubric drafts; terminology and tone calibration | Giving the final authoritative answer with no evidence gate; doing multi-file engineering alone |
| Construction hand | Filesystem, shell, tests, visible errors, iterative repair | HTML, JSONL, scripts, validators, batch generation, packaging, mechanical refactors | Final professional judgment; publishing on its own |
| Red-team / reviewer eye | Hard review, counterexamples, methodology, safety, statistics, boundaries | Read-only fault-finding, blockers, revision-priority lists | Privately changing direction; sending the final draft for the orchestrator |

## Model / body adaptation table (by shell and loop)

This is current practice, not a permanent law. When judging any one daemon, look
at **base model + shell + loop** together.

### 1. GPT / strong generalist model

- **Strengths**: cross-domain synthesis, schema, rubric, experiment design, task
  breakdown, collapsing messy goals into an executable plan.
- **Use for**: fixing structure first — fields, task splits, eval metrics,
  control groups, argument lines.
- **Boundary**: if it is only a plain LLM daemon, do not have it carry a large
  multi-file job alone; and do not treat its plausible-sounding "facts" as
  verified evidence.

### 2. MiMo / Chinese-semantic, human-expression model

- **Strengths**: natural Chinese, close to human expression, scene realism,
  semantic drafts, style calibration, text that needs warmth and local feel.
- **Use for**: small-batch semantic drafts, user-readable phrasing, tone
  calibration, scene-based first drafts.
- **Boundary**: natural tone is not evidence; with no file-construction loop, do
  not have it carry long HTML/JSONL/script bundles. (Watch a known
  small-`max_tokens` truncation trap on some self-hosted setups — verify output
  is not cut off.)

### 3. Grok / OpenRouter xAI-type red-team and evidence-gate model

- **Evidence level**: preliminary (low–medium). Based on a single-day, one-
  sample-per-category routing probe (see
  [`references/grok-routing-probe.md`](references/grok-routing-probe.md)). This
  is a routing note, **not** a benchmark claim.
- **Fit for**:
  - Red-team review — finding category errors, refusing to fabricate
    references, turning a plausible-looking task into questions that need
    verification.
  - Boundary / counterexample probing.
  - Creative expression and short story-style explanation.
  - Long-form critique.
  - Evidence-gate assistance: on de-identified, aggregated, non-private material,
    generating candidate seeds for the orchestrator / a domain expert to accept.
  - Generalist-architect deputy: schema, plan, structured summary, strict JSON.
- **Not fit for**:
  - An unverified authoritative source of fact.
  - Medical / legal certainty conclusions.
  - Directly auto-executing actions with side effects.
  - A high-frequency, low-latency construction slot — the probe showed higher
    latency and a high reasoning-token share, so it is not economical for short
    high-volume work.
- **Privacy boundary**: anything containing real cases, private logs,
  credentials, or un-redacted source text must **not** be sent directly to an
  external Grok / OpenRouter endpoint. De-identify, aggregate, and run a secret-
  shape scan locally first, and record the send boundary in the report.

### 4. MiniMax / creative-expression and media-leaning model (candidate slot)

- **Evidence level**: low to medium. This slot is inferred from a tool catalog
  and prior impression; it has not been through a local controlled experiment.
  Do not write it as law.
- **Candidate strengths**: gentle copy, voice-over scripts, short-video scripts,
  story-style explanation, humanized expression, TTS / audio / multimedia
  prompts, making content "sound like a person talking".
- **Use for**: tasks needing human feel, shareability, media flavor, spoken
  style, creative variants; usable first as a "copy and media-flavor" trial slot.
- **Boundary**: not for rigorous evidence judgment, code construction,
  validators, statistical method, complex multi-file engineering, or final
  academic / clinical / legal conclusions. To promote it to a formal route, run a
  small A/B task validation.

### 5. Zhipu / GLM-type hard-review model

- **Strengths**: hard review, structural fault-finding, method/protocol,
  statistical sensitivity points, safety boundaries, counterexamples and a
  reviewer's perspective.
- **Use for**: read-only fault-finding, blocker lists, major/minor triage, risk
  lists, 48h revision priorities.
- **Boundary**: a red-team eye should not set the final direction for the
  orchestrator; not a main construction hand.

### 6. Claude Code / code agent with a file-construction loop

- **Strengths**: writing to disk, shell, tests, validators, HTML/JSONL/report
  generation, screenshots, zips, seeing an error and repairing it.
- **Use for**: anything that "must be written to disk, can run tests, needs
  mechanical checking" — prefer the construction hand.
- **Boundary**: construction ability is not domain truth; its output must be
  re-checked by the orchestrator and any needed semantic / red-team daemon.

### 7. Kimi Code / fast coding-grunt construction body

- **Strengths**: small-to-medium code edits, scripts, local refactors, repeated
  validator / test repair, and other mechanical construction work where fast
  file-level iteration matters.
- **Use for**: implementation candidates, glue code, repo maintenance, local
  project edits, and repeated verification loops after the orchestrator has
  fixed the task boundary, files to touch, forbidden side effects, and acceptance
  checks.
- **Boundary**: Kimi is a construction hand, not the owner of product intent,
  clinical / academic truth, credential safety, or public-release authority. The
  orchestrator still frames the task, protects secrets, re-runs key validation,
  and controls commit / push / merge.
- **Evidence cue**: recent LingTai practice used Kimi Code as a code-grunt body
  for local construction and verification; keep recording when it works, where
  it fails, and what the main body had to recheck.

### 8. Codex / coding-CLI body

- **Strengths**: codebase navigation, patches, tests, refactors, deterministic
  verification, software-engineering-style construction.
- **Use for**: repo patches, test-driven fixes, code audits, command-verifiable
  engineering problems.
- **Boundary**: do not entrust critical tasks when local auth / credentials are
  unstable; do not output the final human narrative with no review.

### 9. Plain LLM daemon (few or no tools)

- **Strengths**: short ideas, an onlooker's mirror, local summaries, alternative
  phrasing, one-shot reasoning.
- **Use for**: low-noise small tasks that need only a conclusion, no disk write,
  no validation.
- **Boundary**: not for large multi-file engineering; if the task grows, switch
  to small batches + a construction hand + a validator.

### 10. Orchestrator / main body

- **Strengths**: continuous memory, human intent, channel discipline, the
  evidence gate, the public boundary, the final narrative.
- **Use for**: goal clarification, task split, acceptance, evidence verification,
  reporting back on the original channel, distilling skills / knowledge.
- **Boundary**: the orchestrator should not personally swallow every large log,
  large file, and long scan — push noise to a daemon or a script.

## Workflow

1. **Frame the task and red lines.** Orchestrator fixes the goal, the evidence
   gate, and the boundaries (public, attribution, privacy).
2. **Pick slots, not models.** Map the work onto the five slots; choose a body
   for each by base model + shell + loop.
3. **Write the construction contract** (below) for any deliverable larger than a
   short answer.
4. **Ship in small batches.** 3–5 units per batch, not one big pour. Update a
   PROGRESS file and run the validator after each batch.
5. **Gate before delivery.** Route through the red-team / evidence gate; the
   orchestrator does final acceptance and replies to the human.

### Construction contract for large / long tasks

If the artifact exceeds one short answer (a long report, a multi-file bundle,
10+ cases, HTML, a dataset, a test suite), state clearly:

1. **Output directory** — where all artifacts are written.
2. **Batch size** — 3–5 units at a time, not one pour.
3. **PROGRESS** — update `PROGRESS.md` or `status.json` per batch.
4. **Validator** — auto-checks: field completeness, duplicate IDs, secret shapes,
   external links, format, red lines.
5. **Verification commands** — list the commands that must run.
6. **Forbidden actions** — no network, no outbound comms, no publishing, no
   delete/modify, no push, unless explicitly authorized.
7. **Stop condition** — if scope changes, stop the current run or open a new one;
   do not keep appending large goals to a running daemon.

### Suggested daemon prompt skeleton

```text
In this task you act only as one of [construction hand / domain brain /
red-team eye / generalist architect]. Do not take on any other slot.

Goal: ...
Input: ...
Output directory: ...
Batch: ... units per batch.
Must write: PROGRESS.md / status.json.
Must run validation: ...
Forbidden: network / outbound comms / push / delete / credential change /
publishing, unless explicitly stated otherwise.
On completion return only: conclusion, paths, validation results, remaining
risks, next step.
```

## Validation

- Output directory has new files after each batch (not just "reading/thinking").
- `PROGRESS.md` / `status.json` is updated per batch.
- The validator passes: fields complete, no duplicate IDs, no secret shapes, no
  broken external links, format and red lines OK.
- All listed verification commands run, with results recorded.
- The red-team / evidence gate has reviewed before any human-facing delivery.

## Failure signals

Do not keep waiting when you see:

- A daemon spends a long time only "reading / thinking" with no new files in the
  output directory.
- No PROGRESS file and no intermediate artifacts.
- The parent keeps appending scope and the daemon keeps re-planning.
- A large-file task was handed to a one-shot LLM with no file loop.
- A red-team daemon starts setting direction or writing the final draft.
- A domain daemon gives an authoritative conclusion with no evidence anchor.

Handling: inspect the run directory → if nothing on disk, reclaim or open a new
executor → switch to a small-batch / construction-hand route → orchestrator
resets the contract.

## Safety and privacy

- Do not mistake tool-construction ability for base-model domain expertise.
- Do not mistake base-model tone for verified fact.
- Do not let a daemon communicate with humans or external channels past the
  orchestrator.
- Do not write one task's experience into an academic-style law ("model X is
  innately good at Y"); to publish such a claim, design an experiment measuring
  completion rate, validator pass, token cost, human scoring, and failure types.
- Do not let "multi-model" substitute for the evidence gate — multi-model is a
  division of labor, not a guarantee of fact.
- Before sending anything to an external endpoint, de-identify, aggregate, and
  run a secret-shape scan locally; record the send boundary in the report. Never
  send real cases, private logs, credentials, or un-redacted source text to an
  external model.

## Attribution

- Author: Runyuan Wang / 9s5bz2jvd2-lang
- Submitted in: Lingtai-AI/lingtai-workflow (PR pending)
- Last verified: 2026-06-27
