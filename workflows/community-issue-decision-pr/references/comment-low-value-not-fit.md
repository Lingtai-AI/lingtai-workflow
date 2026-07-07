# Comment template — LOW_VALUE / NOT_FIT

Use for issues judged `LOW_VALUE` or `NOT_FIT` by `lingtai-taste`. It is **advisory
and ask-first**: it thanks the reporter, gives the concrete fit/layer/scope reason,
and asks the human (Jason) whether to close. It does **not** close the issue and
does **not** state the decision as final.

Fill the bracketed slots. Keep it short and specific; cite the real reason, not a
generic "won't do".

```markdown
Thanks for taking the time to write this up, @<reporter> — the report is clear and
the behavior you describe is real.

After looking at it against how this repo draws its boundaries, I don't think this
is the right change to make here, for this reason:

> <one concrete reason — e.g. the current behavior violates no documented
> invariant, so tightening it would be a behavior change rather than a bug fix; or
> the fix belongs at <owning layer> rather than here; or the new
> flag/abstraction/opt-out adds surface without a capability the existing surfaces
> can't already reach.>

<Optional: what would change this — e.g. "If you can show a case where <invariant>
is actually violated, that would move it into scope.">

I'm not going to close this myself — @<maintainer/Jason>, do you want to close it,
or keep it open for a second look?
```

## Notes

- Post this only after the issue decision and comment draft have been audited by Codex CLI and re-reviewed by GLM and Kimi, or after the missing review has been explicitly escalated to the human.
- Never imply the decision is already made or that the issue "will be closed".
- Do not paste internal reasoning that names private paths, logs, or secrets.
- If the reason is genuinely a maintainer direction call, prefer
  `NEEDS_CLARIFICATION` and ask the direction question instead of asserting a
  fit judgment.
