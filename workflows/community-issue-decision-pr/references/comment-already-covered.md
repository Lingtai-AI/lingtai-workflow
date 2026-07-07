# Comment template — ALREADY_COVERED / DUPLICATE

Use for issues judged `ALREADY_COVERED` (main already does this / a merged change
supersedes it) or `DUPLICATE` (same as another issue). It **links the real
covering or canonical artifact** and asks the human to confirm close/link. It does
**not** close the issue.

Verify the link through GitHub before posting — an unverified "already covered" or
"duplicate" claim is worse than no comment.

## Already covered

```markdown
Thanks, @<reporter>. I believe this is already handled on `main` as of
<commit/PR link — e.g. #<PR> / <sha>>, which <one line on what that change does
that covers this>.

Can you confirm the behavior you're seeing on the latest `main`? If it's still
reproducing there, that's a different bug and I'll re-open the investigation.

@<maintainer/Jason> — assuming it's covered, do you want to close this as
resolved, or keep it open until <reporter> confirms?
```

## Duplicate

```markdown
Thanks, @<reporter>. This looks like the same underlying issue as
#<canonical-issue>, so I'd suggest we track it there to keep the discussion in one
place.

<Optional: one line on any detail from this report worth carrying over to the
canonical issue.>

@<maintainer/Jason> — want me to leave this open and linked, or close it as a
duplicate of #<canonical-issue>?
```

## Notes

- Post this only after the issue decision and comment draft have been audited by Codex CLI and re-reviewed by GLM and Kimi, or after the missing review has been explicitly escalated to the human.
- Always link the real covering change / canonical issue; never assert coverage
  from memory.
- Ask the human before closing; offer "keep open until the reporter confirms" as
  a default when coverage isn't yet confirmed on the reporter's side.
