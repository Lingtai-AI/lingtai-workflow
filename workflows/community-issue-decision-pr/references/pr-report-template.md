# PR / report template — GOOD issues

Use for issues judged `GOOD`. Fill the slots, paste **literal** command output
into Validation, and open the PR **unmerged** — merge is the human's decision.
(The outer fence below is `~~~` so the inner ` ``` ` command block renders.)

~~~markdown
<Conventional Commit title, e.g. fix(<area>): <short description>>

Addresses: #<issue>   <!-- do not use closing keywords unless Jason explicitly authorizes linked auto-close -->

## Taste decision

- Decision: GOOD
- Themes: <e.g. root-cause-not-symptom, fix-at-the-owning-layer, smallest-honest-scope>
- lingtai-taste version: <mined: date / commit>

## Summary

- Root cause: <where the invariant is first violated — not the symptom>
- Fix: <the smallest-scope change that closes the real gap>
- Non-goals: <what this PR deliberately does not do>

## Validation

```
$ <test command>
<literal output>

$ <validator, e.g. python3 scripts/validate_workflow_skills.py>
<literal output>

$ git diff --check
<literal output — empty means clean>
```

## Reviews

| Reviewer | Verdict | Notes / unresolved blockers |
|---|---|---|
| Claude Code (writer) | candidate | <what it built> |
| Codex CLI (audit) | <pass / blockers> | <...> |
| GLM (review) | <pass / blockers> | <...> |
| Kimi (review) | <pass / blockers> | <...> |
| Parent (synthesis) | <PR-ready / not> | <how contradictions were resolved> |

## Risk / rollback

- Risk: <what could break>
- Rollback: <how to revert — usually revert this PR>

## Merge

Opened for review; **not merged**. Merging is @<maintainer/Jason>'s call.
~~~

## Notes

- Paste real command output; do not write "tests pass" without the evidence.
- If any required review is missing (reviewer unavailable / over quota), mark it
  explicitly in the Reviews table as not-done rather than leaving it blank or
  implying it passed.
- Ship a vertical slice: fix + failing-first regression test + docs/anatomy +
  locales the repo expects. A fix with no regression test is not PR-ready.
- Do not include raw secrets, private logs, mail IDs, or PII in the PR body.
