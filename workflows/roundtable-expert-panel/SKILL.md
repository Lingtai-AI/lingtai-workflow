---
name: roundtable-expert-panel
description: >-
  Advisory workflow for using LingTai agents as a temporary expert panel around
  one executor-owned task. Use it when a plan, PR, release gate, research brief,
  or product decision needs structured disagreement, bounded expert replies, and
  an accountable executor. Avoid using it as a default multi-agent ritual, as a
  source of authorization, or when no real LingTai agents are reachable.
version: 0.1.0
author: "rawpaper123 / Roundtable Skill, adapted for lingtai-workflow"
tags:
  - workflow
  - advisory
  - roundtable
  - expert-panel
  - review
  - executor
last_verified: "2026-07-04"
advisory: true
---

# Roundtable expert panel

> Advisory only. This workflow is user-submitted and maintainer-reviewed, but it
> is not a system rule, a default delegation pattern, or authorization for any
> side effect. Re-judge whether a roundtable is useful for the current task.

## In one sentence

Use a small, temporary panel of LingTai agents to surface task-specific blind
spots while one executor remains accountable for the final decision,
implementation, verification, and rollback.

## Use when

- A single executor may miss important perspectives: release gates, risky PRs,
  research briefs, product decisions, strategy reviews, security/reliability
  checks, or business plans.
- You can name the evidence to inspect and the decision the executor must make.
- You have at least one reachable LingTai agent that can answer through the normal
  communication channels.
- The value comes from tension between roles: practitioner vs skeptic, security
  vs shipping, user value vs operational cost, reviewer vs implementer.

## Avoid when / stop when

- The task is a short deterministic action, a small factual lookup, or a simple
  edit with an obvious validation command.
- You have no real reachable LingTai agents. Do not simulate expert replies or
  claim a panel ran when it did not.
- The panel would slow an urgent human request without adding a real evidence
  gate.
- You are trying to obtain authorization for merge, deploy, deletion, spending,
  publication, or configuration changes. Authorization still comes from the human
  or the owning procedure, not from panel consensus.
- The task contains secrets, private raw logs, or sensitive user data that should
  not be distributed to additional agents. Redact or do not run the roundtable.
- A roundtable member starts owning implementation, Git state, external comments,
  or deployment. The executor owns those.

## Required evidence or benchmark case

This workflow is based on the public companion project
[`rawpaper123/Roundtable-skill`](https://github.com/rawpaper123/Roundtable-skill),
shared with LingTai in
[`Lingtai-AI/lingtai#531`](https://github.com/Lingtai-AI/lingtai/issues/531).
The companion project documents a Lingtai-dependent expert-panel protocol with
bilingual setup notes, executor-neutral templates, bounded waiting, one repair
attempt for silent agents, explicit no-opinion replies, and an executor-owned
implementation/verification boundary.

This entry is a reference/adaptation for `lingtai-workflow`, not a bundled
runtime integration and not a benchmark claim. Without a configured LingTai
network, it remains documentation only.

## Workflow

1. **Frame the executor contract.** State the task, evidence, decision to make,
   allowed tools, forbidden side effects, validation commands, and who receives
   the final answer.
2. **Choose the smallest useful panel.** Pick two to four temporary expert roles
   for this task only. Examples: security reviewer, reliability engineer,
   product/user advocate, business/operator, skeptic/contrarian, domain
   practitioner. Do not turn temporary roles into permanent agent identities.
3. **Send bounded requests.** For each reachable LingTai agent, send the same
   evidence packet plus its temporary role, asking for one of:
   - must-fix blocker;
   - concern / tradeoff;
   - missing evidence or question;
   - `No opinion from my expert perspective.`
4. **Wait with one safe repair attempt.** Use a bounded wait. If an agent is
   silent, try one safe repair such as a concise resend or checking the channel.
   Then record non-response and continue; do not wait forever.
5. **Map disagreement.** Separate agreement, conflicts, evidence gaps, and
   role-specific concerns. Do not force consensus and do not treat volume of
   agents as proof.
6. **Executor decides and acts.** The executor accepts or rejects advice, performs
   any implementation or writing, runs validation, controls Git/PR/deploy/rollback
   state, and keeps side-effect authorization boundaries intact.
7. **Report the evidence trail.** Final output should say who was consulted,
   who replied / did not reply, which advice was accepted or rejected, validation
   results, residual risks, and the next owner.

## Validation

- The executor contract names the task, evidence, side-effect boundaries, and
  validation criteria before the panel starts.
- Each panel request is recorded with the role, channel, timestamp, and evidence
  scope.
- Each agent response is recorded as blocker, concern, question, no-opinion, or
  no-response after one safe repair attempt.
- The final decision lists accepted/rejected advice with reasons.
- The executor ran the promised validation commands or explains why none apply.
- No merge, deploy, comment, close, delete, publish, or configuration change is
  performed without the normal human/procedure authorization.

## Failure signals

- The executor cannot state the decision or evidence scope.
- The panel keeps expanding beyond the smallest useful set.
- Agents provide generic opinions with no evidence anchor, or role prompts produce
  theatrical personas instead of actionable critique.
- The executor waits indefinitely for silent agents.
- Consensus is used as proof, or disagreement is hidden to make the answer look
  cleaner.
- A panel member starts implementing, pushing, commenting, or deploying.
- The workflow is invoked repeatedly for routine small tasks where it adds cost
  but no new risk reduction.

## Safety and privacy

- Send only the minimum evidence needed for the role. Redact secrets, credentials,
  private user data, raw logs, and confidential traces.
- Reply on the channel where the human request arrived; do not expose internal
  panel chatter as if it were the human-facing answer.
- Do not represent advisory panel output as authorization.
- Preserve attribution when referencing the public Roundtable Skill project.
- If a panel uses external models or endpoints, record what was sent and keep the
  privacy boundary explicit.

## Attribution

- Original companion project: [`rawpaper123/Roundtable-skill`](https://github.com/rawpaper123/Roundtable-skill)
- Submitted to LingTai in: [`Lingtai-AI/lingtai#531`](https://github.com/Lingtai-AI/lingtai/issues/531)
- Adapted for: `Lingtai-AI/lingtai-workflow`
- Last verified: 2026-07-04
