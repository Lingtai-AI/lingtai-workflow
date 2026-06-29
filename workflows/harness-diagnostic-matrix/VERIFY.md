# VERIFY — harness-diagnostic-matrix

Date: 2026-06-29. Environment: local, no network, no commit, no push.
All paths below are relative to the workflow folder `workflows/harness-diagnostic-matrix/`.

## Commands run and results

| # | Command | Result |
|---|---|---|
| 1 | `python3 scripts/render_harness_matrix.py examples/example_harness_matrix.json examples/example_harness_matrix.html` | **PASS** — exit 0, wrote HTML (5 rows). |
| 2 | `python3 -m json.tool examples/example_harness_matrix.json >/dev/null` | **PASS** — exit 0, valid JSON. |
| 3 | `python3 -m json.tool schema/harness_diagnostic_matrix.schema.json >/dev/null` | **PASS** — exit 0, valid JSON. |
| 4 | `python3 html.parser` feed on rendered HTML | **PASS** — parses with no exception. |

## Static scans

| Scan | Pattern | Result |
|---|---|---|
| Self-contained HTML | `https?://`, `<script`, `<link`, `<iframe`, `cdn.`, `src=` in rendered HTML | **NONE** — no external resources. |
| Secrets | `sk-…`, `api[_-]?key`, `secret`, `bearer`, `password`, `token=`, `AKIA…`, `BEGIN` (PEM) | **NONE as values.** The words `secret`/`token`/`password` appear only as documentation prose in SKILL.md / README.md instructing that secrets be kept out. No secret values. |
| Local/private paths | local absolute path patterns and private workspace markers | **NONE** in the workflow folder. |
| Fix/plan language in matrix rows | `first PR`, `action card`, `rollback`, `implementation plan`, `修复方案`, `实施计划`, `操作卡片` | **NONE in data rows.** The only hit is the HTML boundary note that *states the matrix excludes* fix plans (intended). |

## Evidence-gate behavior

- The renderer's `validate()` warns when a row has a `hypothesis` but no `evidence` and is not flagged `insufficient_evidence`. Hard-fails only on missing structural fields (`harness`, `rows`, required row fields).
- The example exercises both confident rows (with evidence pointers) and `insufficient_evidence: true` rows (401 intermittent; vague maintainer complaint), demonstrating the "no guessing" path.

## Notes / caveats

- The schema is JSON Schema draft-07 for documentation and external validation; the renderer does its own light stdlib validation (no `jsonschema` dependency) to stay dependency-free.
- The renderer accepts both English and Chinese severity/confidence tokens.
- HTML rendering was validated structurally (parser + resource scan); visual layout was not screenshot-verified in this run.


## Additional parent hardening (2026-06-29)

The workflow now includes a mandatory invoking-agent self-test:

```bash
python scripts/selftest_harness_matrix.py
```

An agent must run this itself before applying the workflow to a real harness. PASS means the renderer can generate an HTML matrix from a fresh arbitrary harness input; it is not a substitute for evidence in the real diagnosis.

## Parent validation run (2026-06-29)

Additional parent verification after 圆酱's correction that the skill must make the invoking agent run a self-test:

```bash
python scripts/selftest_harness_matrix.py
python scripts/render_harness_matrix.py examples/example_harness_matrix.json examples/example_harness_matrix.html
```

Observed self-test output: `SELFTEST PASS: rendered selftest_matrix.html from a fresh arbitrary harness input (2 rows).`

This is now a hard usage gate in `SKILL.md`: an agent invoking the workflow must run the self-test itself before applying the matrix to a real harness; otherwise it must stop and report failure.
