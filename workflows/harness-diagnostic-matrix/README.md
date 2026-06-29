# Harness Diagnostic Matrix

> **矩阵在于诊断；如何做，是人的事。**
> The matrix locates problems. *How to fix them is the human maintainer's matter* and is out of scope.

A reusable LingTai workflow skill that turns a fuzzy harness complaint into a structured, evidence-backed **diagnostic matrix diagram** — for any harness (eval, clinical/nutrition, LLM benchmark, code-test, data pipeline, product demo, agent runtime, …).

This is **advisory only**: it is not part of the LingTai runtime or kernel contract, not a model ranking, and never overrides human instructions or task contracts.

## Purpose

Take "it's slow / expensive / flaky / stuck / wrong / I-can't-tell-where" and produce a one-screen matrix where every row is:

| symptom | system site | evidence pointer | likely cause / problem | differentials | next evidence / question | severity | confidence |
|---|---|---|---|---|---|---|---|

It is a **diagnosis**, not a fix plan. There is deliberately no "how to fix" column anywhere — that is the human maintainer's job.

## When to use

- A user/maintainer/engineer reports a vague harness problem and you need to localize it before touching code.
- You want to triage several symptoms at once and see which node each lands on.
- You need a shareable, low-token artifact showing what was checked, the evidence, and what is still unknown.

## When **not** to use

- Someone wants a fix plan, PR sequence, implementation steps, or action cards — that is explicitly out of scope. Hand back to the maintainer.
- The complaint is already a confirmed single-cause bug with a known fix.
- You would need to read private raw messages, secrets, or whole logs to fill it — record the missing evidence and stop instead.

## Evidence gates (why it won't just make things up)

- Every cause/problem hypothesis must carry an **evidence pointer** (log id, wake/turn index, `file:line`, metric, error head/tail, config diff, user snippet).
- If evidence is thin, the row is flagged **insufficient evidence** rather than guessed into a conclusion.
- Competing causes are listed as **differentials**; the "next" column is always *evidence to collect / a question to answer*, never a repair step.
- The examined **scope** is recorded so readers know what was *not* read.


## Mandatory self-test

This workflow is not complete unless the invoking agent runs the self-test itself before using it on a real harness:

```bash
cd workflows/harness-diagnostic-matrix
python scripts/selftest_harness_matrix.py
```

Expected result begins with `SELFTEST PASS`. If it fails, stop; do not produce a final matrix. The self-test generates a matrix from a fresh synthetic harness input, proving that the renderer path is actually runnable.

## Quickstart

```bash
# 1. Write a diagnosis JSON conforming to schema/harness_diagnostic_matrix.schema.json
#    (start from examples/example_harness_matrix.json)

# 2. Render a self-contained HTML matrix diagram (no deps, no network):
python3 scripts/render_harness_matrix.py examples/example_harness_matrix.json out.html

# 3. Open out.html in a browser. Deliver out.html + the JSON.
```

Required per row: `symptom`, `site`, `evidence`, `hypothesis`. The renderer lightly validates structure and warns when a hypothesis row has neither evidence nor an insufficient-evidence flag.

## Generated outputs

- **`<name>.json`** — the structured diagnosis, conforming to `schema/harness_diagnostic_matrix.schema.json`.
- **`<name>.html`** — a single self-contained HTML matrix diagram: no external JS/CSS, no network, dark professional Chinese UI, node strip + matrix table + boundary note.

## Bundle contents

| File | What it is |
|---|---|
| `SKILL.md` | The skill: trigger description, evidence gates, the "no fix plan inside the matrix" rule, and the call workflow. |
| `schema/harness_diagnostic_matrix.schema.json` | JSON schema for the diagnosis input/output (diagnosis-only fields). |
| `scripts/render_harness_matrix.py` | Stdlib-only renderer: `python3 scripts/render_harness_matrix.py in.json out.html`. |
| `examples/example_harness_matrix.json` | Generic, sanitized example (a clinical-nutrition eval harness), with real hypotheses, evidence pointers, and uncertainty flags. |
| `examples/example_harness_matrix.html` | The rendered example output. |
| `VERIFY.md` | What was run and the pass/fail results. |

## Safety

No network, no commits, no external messages. Keep secrets, tokens, private absolute paths, internal mail IDs, and private raw text out of the JSON and HTML.

— Author: Runyuan Wang / 9s5bz2jvd2-lang. Advisory; last verified 2026-06-29.
