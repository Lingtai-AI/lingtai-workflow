# Grok routing probe — preliminary note (de-identified)

> **Status: preliminary routing note, not a benchmark claim.** One sample per
> category, single temperature (0.4), single day, single endpoint. Use for an
> initial routing judgment only, not as a permanent law. To promote any slot to
> a formal route, re-test the relevant categories with 3–5 samples each.

- **Date**: 2026-06-27
- **Provider**: OpenRouter-style xAI endpoint
- **Model under test**: a `grok-4.3`-class model
- **Call volume**: 8 chat completions (one per category), well under a small
  hard cap. No keys, tokens, or credentials are recorded here.

## What was probed

Eight category probes covering the slots this workflow cares about:
architecture/plan, Chinese copy, red-team review, code + strict JSON,
evidence/anti-hallucination, long-context summary, creative expression, and a
tool-call-style strict-JSON output.

The prompts used a **generic, de-identified placeholder task** (collating
scattered cost-evidence for a hypothetical publishable paper, with a deliberate
methodological trap). No real cases, private logs, or un-redacted source text
were sent.

## Observed result (this single round)

All 8 probes returned HTTP 200, `finish_reason=stop`, no degradation, no
truncation. Output quality was broadly high and stable. The standout was not any
single peak capability but a **reliable generalist with evidence hygiene**:

| Category | Result | Observation |
|---|---|---|
| Evidence / anti-hallucination | strong | Refused to invent references, stating they do not exist; separated a domain-specific claim from a broad cross-domain figure; pointed at a verification path. The trap question was answered best. |
| Red-team review | strong | Caught the core methodology error — equating a narrow, decades-old billing-audit figure with a domain-wide error cost is a category error; flat population scaling is invalid. Clear blocker/major/minor triage. |
| Architecture / plan | good | Produced a valid draft-07 JSON schema plus a work plan with reasonable fields. |
| Strict JSON output | good | Pure JSON, no extra prose, parses cleanly. Suits tool-call-style pipelines. |
| Long-context summary | good | Clean Goal/Done/Blockers/Next structure; facts preserved accurately. |
| Code / JSON | good | A small validation function with the target signature, correct logic, runnable. |
| Chinese copy | good | Gentle, natural, no marketing tone, accurate — **but** spent a large reasoning-token overhead for a ~50-character rewrite; poor cost efficiency. |
| Creative expression | good | A concrete, restrained short scene, within the length limit. |

## Weaknesses / failure modes

1. **High reasoning-token overhead (main weakness).** A large share of completion
   tokens this round were reasoning tokens — even short confirmations or a 50-
   character Chinese rewrite ran internal reasoning, roughly tripling completion
   cost and lengthening latency.
2. **Higher, less stable latency.** Several seconds per call on average. Not for
   sub-second or high-concurrency interactive slots.
3. **Uneconomical for light tasks.** The lighter the task, the more lopsided the
   reasoning overhead and the lower the per-unit value.
4. **Untested this round (do not assume).** Multi-turn tool-call stability, true
   very-long-context fidelity, and format discipline at high temperature have no
   evidence yet.

> No API failures, empty content, unparseable JSON, or truncation occurred this
> round: 8/8 success.

## Recommended routing (with evidence level)

- **Primary**: red-team review + evidence gate. Evidence level **medium** — both
  trap questions were answered best and cross-confirmed each other.
- **Secondary**: generalist-architect deputy (schema, plan, structured summary).
  Evidence level **low–medium**; hand its drafts to a cheaper model for bulk
  refinement to avoid burning reasoning tokens.
- **Not recommended**: high-frequency construction or low-latency interactive
  slots; bulk short-copy slots (usable but uneconomical).

## Privacy boundary

Anything containing real cases, private logs, credentials, or un-redacted source
text must **not** be sent directly to an external Grok / OpenRouter endpoint.
De-identify, aggregate, and run a secret-shape scan locally first, then record
the send boundary in the report. In this probe a sanitizer redacted persisted
text and no key / Bearer / token was written to any artifact; keys were passed
only via environment variables and never printed or logged.

## Limits and next steps

- One sample per category; low evidence. To formalize the red-team / evidence-
  gate route, re-test those two categories with 3–5 samples each.
- Untested: multi-turn tool-call stability, true long-context fidelity, high-
  temperature format discipline.
