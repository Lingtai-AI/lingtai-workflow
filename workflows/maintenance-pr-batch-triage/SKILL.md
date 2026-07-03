---
name: maintenance-pr-batch-triage
description: >-
  Advisory workflow for triaging a burst of small maintenance/refactor PRs from
  one contributor before deciding which need full review, which are merge-order
  sensitive, and which should be rejected as abstraction-for-abstraction's sake.
version: 0.1.0
author: "mimo-1; compiled from Jason H review guidance and TZZheng maintenance PR batches"
tags:
  - workflow
  - advisory
  - pull-request-review
  - maintenance
last_verified: "2026-06-30"
last_changed_at: "2026-06-30T21:10:00Z"
advisory: true
---

# Maintenance PR batch triage

> Advisory only. This workflow is user-submitted and maintainer-reviewed, but it
> is not a system rule, merge authorization, model ranking, or replacement for a
> repository maintainer's judgment.

Use this when a contributor opens many small PRs that claim to be
behavior-preserving maintenance: helper extraction, duplicate removal, stale doc
refresh, test-fixture cleanup, persistence helper reuse, daemon/process cleanup,
provider wrapper cleanup, or addon wrapper cleanup.

The goal is **not** to rubber-stamp the batch. The goal is to turn "many small
PRs" into a reviewable queue: what each PR does, what contract it must preserve,
what validation is enough, which PRs are risky, and where the reviewer should
stop.

## Use when

- One contributor opens a burst of small maintenance/refactor PRs against the
  same repository.
- The human asks what each PR does before deciding whether to review, comment, or
  merge.
- The PRs are probably independent but may conflict or overlap after the first
  one merges.
- You need a concise human explanation before spending expensive review effort.

## Avoid when / stop when

- The PRs add user-visible features, schema migrations, security/auth behavior,
  releases, deployment, or irreversible external side effects. Those need their
  own design/review workflow.
- The human asked for a full merge-gate review of one PR, not a batch triage.
- A PR's purpose is unclear from its body and diff stats; ask for clarification
  or run a focused review before summarizing it as safe.
- The batch is "dedupe for dedupe's sake" and the new shared abstraction has no
  independent value. Stop and flag it rather than accepting abstraction churn.
- Any PR touches raw runtime data, secrets, credentials, or user logs; switch to
  a privacy/security review workflow.

## Required evidence or benchmark case

- The workflow was distilled from LingTai maintenance-review practice around
  TZZheng's small cleanup PR batches, including:
  - `lingtai-kernel#577` through `#581`, where `#577`-`#580` were accepted after
    review and `#581` was closed because the deduplication added no independent
    value beyond an unwanted abstraction.
  - `lingtai-kernel#591`, `#592`, and `#599` through `#606`, a later burst of
    daemon, MCP addon, JSONC migration, notification, persistence, provider, and
    docs/anatomy cleanup PRs.
- A useful run produces a table that the human can understand without reading all
  diffs, plus a review plan that separates low-risk docs from high-risk runtime
  surfaces.

## Workflow

1. **Inventory the batch.** Query the open PRs by author/repository. Capture PR
   number, title, URL, draft state, merge state, base branch, head branch, commit
   headline, changed-file count, additions/deletions, and file list.

2. **State the review depth.** Tell the human whether this is only a first-look
   inventory, a focused sanity check, or a full merge-gate review. Do not let a
   first-look explanation sound like merge approval.

3. **Explain each PR in one sentence.** Translate the PR body and file list into
   plain language: "extracts addon config loading," "removes retired
   notification cleanup," "moves token ledger writes to fsutil," and so on.

4. **Classify risk by surface.** Use the highest-risk touched surface, not the
   PR title, as the first routing signal:

   | Surface | Typical risk | Review posture |
   |---|---|---|
   | Docs/anatomy only | Stale or false statements | Check citations/facts; no runtime tests needed unless examples changed. |
   | Single small helper | Hidden behavior delta | Compare old/new call paths and run focused tests. |
   | Migrations/config parsing | Backward compatibility | Add edge-case tests for comments, URLs, missing fields, env names. |
   | Notification/molt/large-result paths | User-visible runtime state | Require focused tests over persistence, dismissal, recovery, and stale state. |
   | Persistence/atomic writes | Data loss/corruption | Check atomicity, append-vs-rewrite semantics, permissions, crash behavior. |
   | Daemon/process/streaming | Hung jobs or lost stderr/events | Check timeouts, process-group cleanup, streaming events, backend-specific paths. |
   | MCP addons/identity/skill wrappers | Integration breakage | Preserve public tool names, envelope shapes, redaction, config env behavior. |
   | Provider/search/vision wrappers | Provider-specific behavior loss | Keep shared construction separate from provider-specific parsing and kwargs. |

5. **Extract the contract each PR must preserve.** Examples:
   - Public wrapper names and result envelopes do not change.
   - Error messages and env/config lookup precedence stay compatible.
   - JSONL appends remain appends; atomic writes remain atomic.
   - Daemon stderr/result/event behavior stays backend-specific where needed.
   - Provider-specific kwargs or response parsing are not over-generalized.

6. **Choose validation before review depth expands.** Start with cheap checks:
   `git diff --check`, changed-file inspection, PR body/file-list consistency,
   and focused tests named by the touched surface. Use Claude/daemon reviewers
   when the batch is noisy, touches runtime surfaces, or the human asks for merge
   readiness.

7. **Reject or defer abstraction churn.** A helper extraction is not good merely
   because it deletes lines. Require one of: repeated bug-prone logic, a stable
   shared contract, clear tests for old edge cases, or a demonstrable reduction
   in future drift. If the abstraction hides important per-surface differences,
   recommend closing or redesigning.

8. **Merge only with authorization, and serialize.** Even when individual PRs are
   clean, merge them one at a time after human authorization. After each merge,
   re-check remaining PR merge state, conflicts, and impacted tests because small
   same-area cleanup PRs often conflict with each other.

9. **Report in two layers.** First send a human-readable inventory/explanation.
   Only then, if asked, run full PR reviews and produce merge/blocker verdicts.

## Human-facing output template

```markdown
I found N open PRs from AUTHOR in REPO. This is a first-look triage, not a
merge-gate review yet.

| PR | What it does | Surface/risk | Suggested next step |
|---|---|---|---|
| #123 | Extracts shared config loader for addons | MCP config compatibility | Focused tests around env/config/error messages |
| #124 | Refreshes stale docs/anatomy | Docs only | Check facts/citations; low risk |

Overall workflow recommendation: review docs/single-helper PRs first; send
notification/persistence/daemon/addon/provider PRs through focused tests or a
review daemon; merge serially only after explicit authorization.
```

## Validation

- Record the exact PR list and timestamp used for the inventory.
- Verify `mergeStateStatus`, branch/base, and file list through GitHub, not memory.
- For each PR selected for deeper review, run at least `git diff --check` and the
  focused tests covering the touched surface.
- If producing a workflow PR from the observation, preserve contributor
  attribution and cite the motivating PR batch without copying private runtime
  data or internal messages.

## Failure signals

- The human asks "can we merge?" and you only have an inventory. Say so and run a
  proper review instead of implying approval.
- Multiple PRs touch the same helper/runtime file and the merge order is likely
  to change diffs.
- Tests pass only because removed behavior is no longer covered.
- A shared helper erases provider/addon-specific behavior, error text, or
  redaction boundaries.
- The review keeps expanding into architecture design; stop treating it as a
  small maintenance batch.

## Safety and privacy

- Do not post GitHub comments, close PRs, merge, push, or edit contributor
  branches without explicit human authorization for that side effect.
- Do not include raw logs, mail IDs, private paths, secrets, or unredacted
  runtime data in public workflow evidence.
- Use repository-visible PR numbers/URLs as evidence; keep private review notes
  in local reports unless the human approves sharing them.

## Attribution

- Compiled by: mimo-1, from Jason H review guidance.
- Motivating contributor examples: TZZheng maintenance PR batches in
  `Lingtai-AI/lingtai-kernel` (`#577`-`#581`, `#591`, `#592`, `#599`-`#606`).
- Submitted in: local draft created 2026-06-30; record the GitHub PR URL in the review thread after submission
- Last verified: 2026-06-30
