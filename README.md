# LingTai Workflow

LingTai Workflow is a user-submitted, maintainer-reviewed catalog of workflow and daemon-tactic bundles for LingTai agents.

This repository is an **advisory reference only**:

- It is not part of the LingTai runtime or kernel contract.
- It is not a model leaderboard and not a fixed routing rulebook.
- It never overrides human instructions, standing rules, tool safety, repository facts, or the current task contract.
- Every workflow must be re-judged against the current task before use.
- Entries may age, fail, be superseded, or be removed.

## Workflow index

Accepted workflows are listed here after review. Each workflow is a self-contained skill-style bundle with a `SKILL.md` file and any supporting `assets/`, `references/`, or `scripts/` it needs.

| Workflow | Use when | Avoid when | Evidence / benchmark case | Author | Last reviewed | Details |
|---|---|---|---|---|---|---|
| maintenance-pr-batch-triage | A contributor opens a burst of small behavior-preserving maintenance/refactor PRs and the maintainer needs a first-look inventory, risk tiering, and merge-order plan | Feature/security/schema/release changes; or when a full merge-gate review is already required for one PR | Distilled from TZZheng maintenance PR batches in `lingtai-kernel` (`#577`-`#581`, `#591`/`#592`/`#599`-`#606`), including closing `#581` as over-deduplication | mimo-1, with Jason H guidance and TZZheng example attribution | 2026-06-30 | [`workflows/maintenance-pr-batch-triage/`](workflows/maintenance-pr-batch-triage/SKILL.md) |

## Submit a workflow

Submit workflows by GitHub pull request. A workflow contribution should:

1. Add a new directory under `workflows/<slug>/`.
2. Include a `SKILL.md` with YAML frontmatter (`name` and `description` are required).
3. Preserve author attribution in the frontmatter and body.
4. Describe when to use it, when not to use it, required evidence or benchmark case, validation, and failure signals.
5. Remove secrets, private paths, internal mail IDs, raw tokens, and private user data.
6. State that the workflow is advisory-only.

See [`templates/workflow-bundle/SKILL.md`](templates/workflow-bundle/SKILL.md) for the starting shape.

## For agents

Agents may suggest creating a workflow PR only at a task boundary, only after a non-trivial reusable workflow has been demonstrated, and only with human consent. Do not interrupt active human work to ask. Do not ask more than once per day.
