---
name: harness-diagnostic-matrix
description: >-
  Generate an evidence-backed diagnostic matrix diagram for any harness
  (evaluation, clinical, benchmark, code-test, data-pipeline, product-demo, or
  agent-runtime) when symptoms are vague and the cause/problem needs locating.
  The matrix diagnoses symptoms, evidence, likely causes, differentials, missing
  evidence, severity, and confidence; it does not prescribe fixes.
version: 1.0.0
author: "Runyuan Wang / 9s5bz2jvd2-lang"
tags:
  - workflow
  - advisory
  - diagnosis
  - harness
last_verified: "2026-06-29"
advisory: true
---

# Harness Diagnostic Matrix

> Advisory only. This workflow is user-submitted and maintainer-reviewed, but it is not a system rule, model ranking, or default authorization. Re-judge it against the current task before use.

> **矩阵在于诊断；如何做，是人的事。** The matrix locates problems. *How to fix them is the human maintainer's matter* and is deliberately out of scope here.

## What this produces

A single self-contained HTML matrix diagram plus the backing JSON, where each row maps:

`symptom / complaint` → `system site` → `evidence pointer` → `likely cause / problem hypothesis` → `differentials (competing causes)` → `next minimal evidence / question`, annotated with `severity`, `confidence`, and an `insufficient-evidence` flag.

It is a **diagnosis**, not a repair plan.

## Use when

- A user, maintainer, or engineer reports a fuzzy harness complaint ("slow", "expensive", "flaky", "stuck", "wrong output", "can't find the problem") and you need to localize it before anyone touches code.
- You want to triage several symptoms at once and see which system node each lands on.
- You need a shareable, low-token artifact that shows what was checked, what the evidence is, and what is still unknown.
- The harness is any kind: eval, clinical/nutrition, LLM benchmark, code-test, data pipeline, product demo, agent runtime.

## Avoid when / stop when

- Someone wants a **fix plan, PR sequence, implementation steps, or action cards** — that is explicitly NOT this skill. Hand back to the human maintainer.
- There is no harness and no complaint (nothing to diagnose).
- You would have to read private raw messages, secrets, or whole logs to fill it — instead, record what evidence is missing and stop.
- The complaint is already a confirmed, single-cause bug with a known fix — a matrix adds nothing.

## Hard rules (evidence gates)

1. **Diagnosis only.** Never put "fix by doing X", "first PR", "rollback", "action card", or "implementation" in any row. If a row needs follow-up, phrase it as *evidence to collect or a question to answer*, never a repair step.
2. **Every cause/problem hypothesis must carry an evidence pointer** (log id, wake/turn index, `file:line`, metric, error head/tail, config diff, user-supplied snippet).
3. **No guessing.** If the evidence does not support a single cause, set `insufficient_evidence: true` and confidence `insufficient` / `unknown`. Do not promote a guess to a conclusion.
4. **List differentials.** Where evidence cannot yet rule out alternatives, name the competing causes.
5. **Bound the evidence.** Record the `scope` you actually examined so readers know what was NOT read. Prefer small windows over full-history reads.
6. **No secrets / no private absolute paths / no private raw messages** in the output artifacts.

## Workflow (the "call" behavior)

1. **Collect** the harness complaint and any offered artifacts (logs, ledgers, configs, a failing case). Ask 3–5 scoping questions if the complaint is vague; do not read everything.
2. **Extract evidence facts** — turn raw artifacts into short, pointer-bearing facts. Note the bounded scope.
3. **Form cause/problem hypotheses**, each tied to an evidence pointer. Where evidence is thin, mark it insufficient instead of guessing.
4. **List differentials and missing evidence** — the competing causes and the next minimal evidence/question that would discriminate them.
5. **Fill the JSON** per `schema/harness_diagnostic_matrix.schema.json`. Required per row: `symptom`, `site`, `evidence`, `hypothesis`.
6. **Render** with the bundled script:

   ```
   python3 scripts/render_harness_matrix.py your_diagnosis.json your_matrix.html
   ```

7. **Deliver** the HTML matrix diagram + the JSON. State the scope and the unknowns. Do not prescribe fixes.

## Generated outputs

- `your_diagnosis.json` — the structured diagnosis (schema-conformant).
- `your_matrix.html` — a self-contained, dependency-free HTML matrix diagram (no external JS/CSS, no network).

See `examples/example_harness_matrix.json` and `examples/example_harness_matrix.html` for a generic, sanitized sample.

## Validation

- `python3 scripts/render_harness_matrix.py examples/example_harness_matrix.json /tmp/out.html` exits 0 and writes HTML.
- `python3 -m json.tool examples/example_harness_matrix.json` and `... schema/harness_diagnostic_matrix.schema.json` both parse.
- The rendered HTML contains no `http(s)://`, `<script>`, `<link>`, or `<iframe>` (self-contained).
- No row contains fix/plan/PR/action language; every hypothesis row has an evidence pointer or an insufficient-evidence flag.

## Failure signals

- You catch yourself writing repair steps → stop; that belongs to the human.
- A hypothesis has no evidence and no insufficient flag → the renderer warns; fix the row.
- You need full logs or private messages to proceed → record the missing evidence and hand back.

## Safety and privacy

- No network, no commits, no external messages from this skill.
- Keep secrets, tokens, private absolute paths, internal mail IDs, and private raw text out of the JSON and HTML.
- The renderer is standard-library Python only; it reads one JSON and writes one HTML, nothing else.

## Attribution

- Author: Runyuan Wang / 9s5bz2jvd2-lang
- Last verified: 2026-06-29
