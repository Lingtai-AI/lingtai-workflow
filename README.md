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
| _No accepted workflows yet._ | | | | | | |

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
