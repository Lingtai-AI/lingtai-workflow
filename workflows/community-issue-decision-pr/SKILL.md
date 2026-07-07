---
name: community-issue-decision-pr
description: >-
  Advisory workflow for community-reported GitHub issues: run each through
  `lingtai-taste`, get Codex/GLM/Kimi review of every decision, open a
  multi-reviewer PR for GOOD issues, leave polite ask-first comments for
  low-value/not-fit/duplicate/already-covered/unclear issues, and escalate
  security-risk issues. No auto-close, auto-merge, or deploy.
version: 0.1.0
author: "Claude Code (main writer), compiled from Jason H handling contract and the lingtai-taste skill"
tags:
  - workflow
  - advisory
  - community
  - issue-triage
  - pull-request
  - multi-model
  - review
last_verified: "2026-07-06"
last_changed_at: "2026-07-07T01:58:30Z"
advisory: true
---

# Community issue decision & PR

> Advisory only. This workflow is user-submitted and maintainer-reviewed, but it
> is not a system rule, a merge/close authorization, a model ranking, or a
> replacement for the maintainer's judgment. Consensus among reviewers is **not**
> authorization: one executor stays accountable, and the human decides every
> irreversible side effect (merge, close, deploy).

Use this when a repo has a queue of **community-reported issues** and the human
wants each one handled to the same bar: decide whether it is worth doing, and
then either open an implementation PR (for good issues) or leave a polite,
explanatory comment that asks the human before any issue is closed. It pairs the
[`lingtai-taste`](#inputs) decision skill (the "should we do this?" judgment)
with the multi-reviewer construction loop (Claude Code writes, Codex CLI audits,
GLM and Kimi re-review, parent synthesizes). The bundle does not vendor
`lingtai-taste`; sync/load that external skill as the decision oracle before
running this workflow.

The goal is **not** to clear the queue by closing or merging things. The goal is
to turn "N community issues" into: a defensible decision per issue, a small
root-cause-scoped PR where the issue is worth doing (opened, not merged), and a
polite ask-first comment where it is not.

## Use when

- A repo has a batch of community/external issues and the human asks for each to
  be triaged and, where good, implemented as a PR.
- You want a consistent decision taxonomy applied across many issues, not ad-hoc
  per-issue judgment.
- The issues are probably independent and can be worked in parallel, but may
  touch overlapping files.
- You have the reviewer bodies available (Claude Code, Codex CLI, GLM, Kimi) and
  the human wants multi-model review before a PR is opened.
- The human has authorized **open PR / comment** but explicitly withheld
  **merge / close / deploy**.

## Avoid when / stop when

- You do not have explicit authorization to open PRs or post comments in the
  target repo. Stop and ask; this workflow never invents that authorization.
- The human asked you to **merge, close, or deploy**. This workflow deliberately
  stops before those. Escalate to the human for the decision.
- An issue needs a design discussion or a maintainer direction call the workflow
  cannot make (behavior change vs bug fix, new public surface, trust-model
  question). Route it to `NEEDS_CLARIFICATION` and hand it to the human.
- The issue or its reproduction data contains secrets, credentials, private
  logs, or user PII. Switch to a privacy/security path; do not paste raw data
  into a public PR/comment or send it to an external reviewer.
- The scope keeps growing inside one issue (it is really several issues, or an
  architecture change). Stop, mark scope-too-broad, and split or hand back.
- Reviewer bodies are unavailable or over quota such that the review contract
  (Codex audit + GLM + Kimi) cannot be met. Degrade honestly (see Failure
  signals); do not silently ship a PR that skipped its reviews.

## Inputs

State these explicitly before starting a run; a missing input is a reason to
pause, not to guess.

- **Issue list / scope** — the exact issue numbers/URLs and repo(s) in scope.
  Bound the batch; do not expand it mid-run.
- **Target repo(s)** — where issues live and where PRs would open; branch base;
  whether the local checkout is fresh (see Failure signals: stale repo/branch).
- **Authorization limits** — what side effects the human has granted. Default
  and required here: **open PR = allowed, comment = allowed; merge / close /
  deploy / push-to-others'-branches = NOT allowed.** Record the exact grant.
- **Taste skill path / version** — the `lingtai-taste` skill location and its
  freshness (`mined:` date). Sync it (`git pull --ff-only`) before applying, and
  record the version used per decision. Taste evolves with the decision record.
- **Reviewer / tool availability** — which of Claude Code, Codex CLI, GLM, Kimi
  are reachable, their quotas, and any privacy limits on external endpoints.
- **Parallelism limits** — how many issues may be worked concurrently, whether
  isolated worktrees/daemons are available, and any repo areas that must not be
  edited concurrently.

## Decision taxonomy

Run [`lingtai-taste`](#inputs) per issue first. Predict the maintainer's decision
**before** spending implementation effort — most refused work is well-built but
refused on fit, layer, trust model, or scope. Every decision below is a first
judgment for the human, not a final action.

| Decision | Meaning | Action (all human-gated for irreversible steps) |
|---|---|---|
| `GOOD` | Real defect / worth-doing improvement; root cause is scoped and the fix fits the owning layer | Open an implementation **PR** (see pipeline). **Do not merge.** |
| `LOW_VALUE` | Correct-ish but not worth the surface/maintenance it asks for (premature abstraction, opt-out flag, belt-and-braces) | Post the polite **low-value / not-fit comment**; ask the human whether to close. **Do not close.** |
| `NOT_FIT` | Out of scope, wrong layer, or a behavior change dressed as a bug fix with no violated invariant | Post the polite **low-value / not-fit comment** explaining the fit/layer reason; ask the human whether to close. **Do not close.** |
| `ALREADY_COVERED` | Main already does this, or a merged change supersedes it | Post the **already-covered comment** linking the covering commit/PR/behavior; ask the human to confirm close. **Do not close.** |
| `NEEDS_CLARIFICATION` | Underspecified, unreproducible, or needs a maintainer direction call | Post a clarifying question to the author and/or hand the direction call to the human. Do not implement on a guess. |
| `DUPLICATE` | Same as another open/closed issue | Post the **duplicate comment** linking the canonical issue; ask the human to confirm close/link. **Do not close.** |
| `SECURITY_RISK` / `SECRET_RISK` | Contains or exposes secrets, credentials, private logs, PII, or is a live security finding | **Escalate to the human.** Limit raw data: do not paste it into public PR/comment or send it to external reviewers. Judge findings against the *declared* trust boundary before calling anything a vulnerability. |

Taste red flags that most often flip an eager `GOOD` to `LOW_VALUE`/`NOT_FIT`
(from `lingtai-taste`): a security claim that assumes an undeclared trust
boundary; wiring "dead" code that was a consciously rejected option; a
"low-risk confinement fix" that violates no documented invariant (behavior
change, not a bug fix); a new opt-out flag or compat shim; a silent heal of bad
state instead of failing loud at the source; centralizing similar-looking
snippets that share no real invariant. When one of these fits, prefer
`LOW_VALUE`/`NOT_FIT` with a clear reason over an implementation PR.

## Per-issue pipeline

Each issue runs this chain independently. The parent (orchestrator) frames the
task, guards the evidence/authorization gate, and makes the final call. Jason's
review contract applies to **every issue decision**, not only to implementation
PRs: Claude Code drafts the decision/PR/comment, Codex audits it, GLM and Kimi
re-review it, and the parent synthesizes before any PR/comment is posted.

1. **Taste decision.** Run `lingtai-taste` on the issue: root cause vs symptom,
   trust model, bug-fix vs behavior-change, guidance-vs-mechanism, surface
   budget, scope, staleness. Record the decision, the themes it turned on, and
   the taste version used. A non-`GOOD` decision skips implementation effort,
   but it does **not** skip Codex/GLM/Kimi review of the decision and comment.

2. **Claude Code draft for the outcome.** Claude Code is the main writer for the
   next artifact, whichever path the taste decision chose:

   - `GOOD`: draft the implementation branch/PR candidate.
   - `LOW_VALUE` / `NOT_FIT`: draft the ask-first explanatory comment.
   - `ALREADY_COVERED` / `DUPLICATE`: verify the covering/canonical link and
     draft the ask-first link/comment.
   - `NEEDS_CLARIFICATION`: draft the clarification question to the author and/or
     the direction question to Jason.
   - `SECURITY_RISK` / `SECRET_RISK`: draft a private escalation summary with
     raw data minimized/redacted; do not draft a public comment that exposes the
     sensitive material. Reviewers review the redacted escalation summary; raw
     sensitive material stays on the private path and is never pasted into public
     PRs/comments or reviewer prompts.

3. **Small root-cause scope (GOOD only).** Re-derive the actual defect where the
   invariant is first violated — not the reported symptom or the literal ask.
   Fix at the owning layer. Define the smallest honest scope, state non-goals,
   and keep it one PR / one concern. If scope balloons, stop and mark
   scope-too-broad.

4. **Codex CLI audit (all decisions).** Codex CLI audits the candidate
   read-first. For `GOOD`, it checks whether the diff closes the real gap, the
   test is genuinely failing-first, public surface/behavior changes are earned,
   and validation passes. For non-`GOOD`, it checks whether the decision follows
   `lingtai-taste`, the comment/clarification is evidence-backed and polite, the
   ask-before-close boundary is explicit, and no sensitive data leaks. Record the
   verdict and blockers.

5. **GLM review (all decisions).** GLM does a hard structural/red-team pass:
   counterexamples, method/protocol, safety boundaries, risk list, major/minor
   triage. For non-`GOOD`, it specifically challenges false `LOW_VALUE`/`NOT_FIT`
   calls and unverified `ALREADY_COVERED`/`DUPLICATE` links. Record the verdict.

6. **Kimi review (all decisions).** Kimi re-reviews for correctness and
   mechanical soundness. For `GOOD`, this is diff/test soundness; for non-`GOOD`,
   it is comment/template correctness, link hygiene, privacy, and whether the
   issue should instead be escalated or clarified. Record the verdict.

7. **Parent synthesis.** The orchestrator reconciles the four perspectives
   (Claude draft/candidate + Codex + GLM + Kimi). It resolves contradictions,
   decides whether the issue outcome is ready to post/open, and owns the final
   judgment — reviewer consensus informs but does not authorize. If reviews
   contradict on a correctness-critical or fit-critical point, do not post/open;
   return to taste/scope/draft or escalate.

8. **PR, comment, or private escalation (no merge/close).** For `GOOD`: open the
   PR using the PR-report template; leave it **unmerged** and note that merge is
   the human's call. For non-`GOOD`: post the matching ask-first comment only
   after parent synthesis says it is ready. For `SECURITY_RISK` / `SECRET_RISK`:
   send the minimized private escalation to the human and wait; do not post raw
   material publicly. Never close the issue automatically.

Reviewer-role details (which body fits which slot, and where each stops) follow
the `multi-model-daemon-orchestration` workflow's slot table; keep Claude Code as
the construction/drafting hand, Codex/GLM/Kimi as read-first review eyes, and the
parent as the accountable orchestrator.

## Parallelism guidance

- **Split independent issues** into isolated worktrees / daemons so their edits
  do not collide. One issue → one branch → one worktree is the safe default.
- **Avoid overlapping edits** to the same files or repo areas. Before fanning
  out, group issues by the files/subsystems they are likely to touch; serialize
  issues that share a hot file rather than merging conflicting diffs later.
- **Respect the parallelism limit** from Inputs; do not exceed the human's
  concurrency cap or reviewer/tool quotas.
- **The parent orchestrates final decisions.** Per-issue daemons produce
  candidates and reviews; the parent synthesizes, opens PRs, drafts comments,
  and reports. Daemons do not open PRs, post comments, merge, or close on their
  own, and do not talk to humans past the orchestrator.
- **No cross-issue authority creep.** A decision on one issue is not
  authorization for another; re-judge each against the current task.

## Comment templates

Templates for the ask-first comments and the PR report live in
[`references/`](references/) so they can be copied without rewriting them:

- [`references/comment-low-value-not-fit.md`](references/comment-low-value-not-fit.md)
  — polite explanation for `LOW_VALUE` / `NOT_FIT`; asks the human before close.
- [`references/comment-already-covered.md`](references/comment-already-covered.md)
  — for `ALREADY_COVERED` / `DUPLICATE`; links the covering/canonical
  commit/PR/issue and asks the human to confirm close/link.
- [`references/pr-report-template.md`](references/pr-report-template.md)
  — PR body / report for `GOOD` issues.

Every comment is polite, thanks the reporter, gives the concrete reason, and ends
by asking the human (Jason) whether to close — it never closes directly and never
implies the decision is already made.

## PR / report requirements

A `GOOD` PR (see [`references/pr-report-template.md`](references/pr-report-template.md))
must carry, at minimum:

- **Issue link** — the community issue it addresses.
- **Taste decision** — `GOOD`, the themes it turned on, and the taste version.
- **`## Summary`** — root cause, the smallest-scope fix, and stated non-goals.
- **`## Validation`** — literal commands run and their results (tests, validator,
  `git diff --check`), not a claim that they were run.
- **Reviewer verdicts** — Codex CLI audit, GLM review, Kimi review, each with a
  verdict and any unresolved blockers, plus the parent's synthesis.
- **Risk / rollback** — what could break and how to revert.
- **No merge** — an explicit note that the PR is opened for the human to decide
  on; the workflow does not merge it.

## Validation

- Record the exact issue list and timestamp used for the batch.
- Verify issue/PR/commit facts through GitHub, not memory: an "already covered"
  claim must link the real covering change; a "duplicate" must link the real
  canonical issue.
- Sync and record the `lingtai-taste` version applied to each decision.
- Record Codex/GLM/Kimi verdicts for **every issue outcome**, including
  non-`GOOD` comments or escalation summaries; do not post an ask-first comment
  until the review contract is met or the missing review is explicitly escalated.
- For each `GOOD` candidate, run the repo's tests, `scripts/*` validators where
  present, and `git diff --check`, and paste the literal results into the PR.
- Confirm each opened PR is **unmerged** and each non-`GOOD` issue is **unclosed**
  before reporting the batch as done.
- Confirm no raw secrets/PII/private logs reached a public PR/comment or an
  external reviewer.

## Failure signals

Return to the parent / human when you see:

- **Reviewer unavailable** — Codex/GLM/Kimi cannot be reached. Do not silently
  ship a PR that skipped a required review; either wait, degrade with the missing
  review clearly marked as not-done, or escalate.
- **Tool quota** — a reviewer/body is over quota. Record which reviews are
  missing; do not pretend they passed.
- **Contradictory reviews** — reviewers disagree on a correctness-critical point.
  Do not ship on majority vote; the parent re-scopes, re-implements, or escalates.
- **Issue scope too broad** — the issue is several issues or an architecture
  change. Stop; split or hand back with a scope note. Do not let a "small fix"
  quietly grow.
- **Sensitive data** — the issue/repro contains secrets/PII. Switch to the
  security path; escalate; limit raw data.
- **Stale repo/branch** — the checkout or a candidate branch was forked from old
  main. Never rebase/revive a stale branch; verify what main already covers, then
  reimplement fresh or mark `ALREADY_COVERED`/superseded with credit.
- **Consensus-as-authorization** — reviewers "all approve", so it feels safe to
  merge/close. It is not. The human decides merge/close/deploy.

## Safety and privacy

- Authorized side effects here are **open PR** and **post comment**, and only
  where this workflow's decision step says so. **Merge, close, deploy, push to
  others' branches, and edit config/secrets are NOT authorized** — escalate to
  the human.
- Never auto-close an issue or auto-merge a PR. Comments ask the human before any
  close; PRs are opened unmerged for the human to decide.
- Do not paste raw logs, credentials, secrets, internal mail IDs, private paths,
  or user PII into public PRs/comments, and do not send them to external
  reviewers. De-identify and run a secret-shape scan before any external send;
  record the send boundary.
- Judge security findings against the **declared** trust boundary before calling
  anything a vulnerability (config flags, addressing modes, and self-writable
  files are not boundaries a design claimed).
- One executor stays accountable. Reviewer/model consensus is division of labor,
  not authorization, and not verified fact.

## Attribution

- Main writer: Claude Code, for this run.
- Compiled from: Jason H's community-issue handling contract, the
  [`lingtai-taste`](#inputs) skill, and the review-slot pattern in
  `workflows/multi-model-daemon-orchestration/`.
- Reviewers in the encoded pipeline: Codex CLI (audit), GLM and Kimi (re-review).
- Submitted in: local draft created 2026-07-06; record the GitHub PR URL in the
  review thread after submission.
- Last verified: 2026-07-06
