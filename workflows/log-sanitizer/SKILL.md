---
name: log-sanitizer-workflow
description: >-
  Advisory workflow for preparing LingTai runtime logs, event traces, daemon
  reports, and exported evidence bundles for sharing without leaking secrets or
  private identifiers. Use it before sending logs/events.jsonl/log.sqlite-derived
  exports, tool-result snippets, or debugging packages to a human, maintainer, or
  external reviewer. It is not a runtime observability system, not an Opik/OpenClaw
  integration, and not proof that sharing is authorized.
version: 0.1.0
author: "Runyuan Wang / 9s5bz2jvd2-lang"
tags:
  - workflow
  - advisory
  - privacy
  - log-sanitizer
  - evidence
  - debugging
last_verified: "2026-06-30"
advisory: true
---

# Log sanitizer workflow

> Advisory only. This workflow is user-submitted and maintainer-reviewed, but it
> is not a system rule, runtime hook, external observability integration, or
> standing permission to share logs. It is a small, local evidence-cleaning
> workflow inspired by the useful boundary in OpenClaw/Opik-style payload
> sanitizers: keep the cleansing habit, not the whole trace platform.

## In one sentence

Before sharing LingTai logs or trace evidence, make a scoped copy, redact secret
shapes and task-specific private literals, verify the outgoing package, and send
only the approved redacted artifact.

## Use when

- A human or maintainer asks for `events.jsonl`, `log.sqlite`, `chat_history`,
  daemon traces, tool-result snippets, or a bug evidence bundle.
- You need to attach evidence to a GitHub issue / PR / discussion without
  leaking credentials, private paths, human names, chat IDs, internal mail IDs,
  or raw tool payloads.
- You are preparing a reproducible debugging package and need a manifest with
  source hashes, redacted hashes, replacement counts, and verification results.
- You want a small local workflow rather than adopting an external trace SaaS,
  SDK, or runtime plugin.

## Avoid when / stop when

- The requester has not been authorized to receive the data. Sanitization does
  not create permission.
- The task requires live runtime instrumentation, trace/span storage, retry
  queues, or dashboards. This workflow is only for local export hygiene.
- You cannot define the recipient, purpose, exact file scope, and retention
  boundary. Ask the human first.
- Verification still finds secret-shaped strings or task-specific forbidden
  literals in the outgoing files. Stop and revise the policy; do not send.
- The files contain regulated or highly sensitive personal data where synthetic
  examples or a schema summary would be enough.

## Required evidence or benchmark case

This workflow comes from repeated LingTai log-sharing pain points: large runtime
files were useful for debugging, but raw exports could carry API keys, private
paths, internal contact IDs, human names, and unrelated third-party context. A
recent manual cleanup showed the smallest reusable value: a deterministic local
sanitizer plus a manifest and verification gate. The benchmark is therefore not
"better observability"; it is **fewer unsafe outbound log packages**.

## Workflow

1. **Fix the sharing contract.** Record recipient, purpose, exact files, allowed
   time range, and who approved the send. If the request is for raw runtime data,
   follow the local approval rule first.
2. **Inventory without copying secrets into chat.** For each source file, record
   path, size, and sha256 in a local manifest. Do not paste raw secret-bearing
   content into the conversation.
3. **Create a redaction policy.** Start from
   [`assets/redaction-policy.example.json`](assets/redaction-policy.example.json).
   Add task-specific `extra_literals` for names, IDs, paths, branch names,
   e-mail addresses, or other strings that must not leave the machine. Add
   `extra_regexes` only when a literal list is insufficient.
4. **Work on a copy.** Never modify the source logs. Write redacted files into a
   fresh output directory.
5. **Run the local sanitizer.** For text / JSONL / Markdown / log files, use
   `scripts/sanitize_export.py`. It can also redact SQLite text columns into a
   copied database and then `VACUUM INTO` a clean output database.
6. **Verify the outgoing package.** Require zero hits for generic secret shapes
   and zero hits for every task-specific forbidden literal. If any hit remains,
   stop.
7. **Package with evidence.** Include the redaction manifest, sha256 sums, and
   policy file. Prefer tar/zip parts only after verification.
8. **Human-facing send gate.** Report what will be sent: file list, hashes,
   redaction status, and known residual risk. Send only after the relevant human
   or project rule authorizes that exact package.

## Local helper scripts

The bundled script is intentionally small and local-first. It is a helper, not a
privacy guarantee.

```bash
python3 workflows/log-sanitizer/scripts/sanitize_export.py \
  --input logs/events.jsonl \
  --input history/chat_history.jsonl \
  --policy workflows/log-sanitizer/assets/redaction-policy.example.json \
  --output-dir /tmp/lingtai-redacted-export
```

Run its self-test before trusting it on a real bundle:

```bash
python3 workflows/log-sanitizer/scripts/selftest_log_sanitizer.py
# SELFTEST PASS: log sanitizer redacted text and sqlite samples.
```

## Validation

- `sanitize_export.py` exits 0.
- `selftest_log_sanitizer.py` exits 0 and prints the PASS line.
- The generated `REDACTION_MANIFEST.json` lists every input, output, replacement
  count, sha256, and verification hit count.
- The verification section reports `generic_secret_hits: 0` and
  `forbidden_literal_hits: 0` for every outgoing file.
- A final grep/scan over the packaged artifact confirms no raw token/password/API
  key shapes and no task-specific forbidden literals remain.

## Failure signals

- The script cannot decode a file and the workflow silently skips it.
- SQLite redaction fails but the original database is still included.
- Output verification has nonzero hits and the agent dismisses them as "probably
  false positives" without human review.
- The agent redacts secrets but leaves human names, private paths, chat IDs, or
  internal mail IDs that the specific recipient should not see.
- The workflow grows into a runtime trace/span platform, SaaS SDK dependency, or
  default always-on logging policy. Stop; this bundle is only export hygiene.

## Safety and privacy

- Sanitization is a **last gate**, not a permission source. If the requester is
  not authorized, do not send even a redacted package.
- Keep original files in place; write only to the output directory.
- Prefer schema summaries, synthetic examples, or minimal excerpts when those
  answer the question.
- Treat names, local paths, chat IDs, internal mail IDs, branch names, and private
  project labels as sensitive when the recipient does not need them.
- Do not send redaction policies containing raw secrets. Use hashes or literals
  only for non-secret identifiers that need removal.
- Do not adopt Opik/OpenClaw SDKs, SaaS, or plugin lifecycle code as part of this
  workflow.

## Attribution

- Author: Runyuan Wang / 9s5bz2jvd2-lang
- Submitted in: Lingtai-AI/lingtai-workflow (PR pending)
- Last verified: 2026-06-30
