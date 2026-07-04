---
name: lingtai-release-blog-publication
description: >-
  Advisory workflow for publishing LingTai release logs after an authorized
  release. Use it to audit full release-window contributors, create the canonical
  `/releases` archive entry, build the site, push to GitHub, and let the web
  repo's automatic deploy run. It hard-codes two repeated release lessons: rejected/closed issue and PR
  authors still count as human contributors, and lingtai-web deploys from GitHub
  push rather than a local wrangler token path.
version: 0.1.2
author: "Jason H / lingtaidev3bot"
tags:
  - workflow
  - advisory
  - release
  - contributors
  - website
  - lingtai
last_verified: "2026-07-03"
advisory: true
---

# LingTai release blog publication

> Advisory only. This workflow is maintainer-requested release practice, not a
> system rule or default authorization. It never overrides the current human
> instruction, repository facts, secret hygiene, or release side-effect boundary.

## In one sentence

When a LingTai release blog/log is authorized, publish it only after a whole-window
public contributor audit that includes rejected/closed issue and PR authors, then
push the web repo to GitHub and let automatic deployment handle the live site.

## Use when

- Jason or a maintainer asks for a LingTai release blog, release log, release-day
  post, or public release notes.
- A TUI/Portal, kernel, addon, or website release is complete or in its publish
  window and needs public bilingual documentation.
- You need to decide who belongs in the public contributor list.
- You have pushed website content and need to reason about deployment.

## Avoid when / stop when

- No maintainer has authorized website publish/deploy side effects.
- The task is a private incident report, PR explainer, or local-only review
  artifact; those do not automatically become public blog posts.
- The contributor evidence includes private identities, secrets, raw internal
  logs, or non-public mail/chat; summarize safely or ask before publishing.
- You are tempted to omit a human because their issue/PR was rejected, closed, or
  unmerged. Stop and include them, or escalate the proposed exclusion before
  publishing.

## Required evidence or benchmark case

This workflow comes from the 2026-07-03 LingTai kernel v0.16.1 + TUI/Portal
v0.10.4 release correction:

- the first blog draft credited commit/merged-PR participants but missed issue
  authors and closed/unmerged PR authors;
- Jason explicitly corrected that issue authors still count even if the issue was
  rejected, and rejected/unmerged PR authors count too;
- Jason also corrected that pushing `lingtai-web` to GitHub automatically deploys
  the site, so a missing local `CLOUDFLARE_API_TOKEN` for `wrangler deploy` is not
  a release blocker;
- Jason then pointed at `https://lingtai.ai/zh/releases/` as the canonical format:
  LingTai release logs belong in the `/releases` archive, not in ad-hoc
  `src/content/blog/release-day-*` posts.

## Procedure

### 1. Confirm release side-effect scope

1. Read the latest maintainer instruction on the original channel.
2. Confirm whether publish is authorized or only a draft/review is requested.
3. Record exact release versions, repo ranges, candidate heads, release URLs, and
   any skipped validations in the task notes.

### 2. Inspect the current website shape

Do not assume old site paths. Inspect the live checkout before editing:

- current release archive and blog content directories;
- localized file naming convention;
- recent release logs and tone;
- build command and deployment expectations.

For the current `lingtai-web`, the canonical release-log surface is the
`/releases` archive. That means adding or updating a `Release` object in
`src/data/releases.ts`, rendered by `src/components/ReleaseDetail.astro`, so the
site generates `/zh/releases/<id>/`, `/en/releases/<id>/`, `/wen/releases/<id>/`,
and `/releases/<id>/`. Do **not** publish `src/content/blog/release-day-*.md` as
the release log. Blog posts are optional companions only when the current website
format explicitly calls for them.

Draft bilingual zh/en release fields when the site supports both.

### 3. Audit public contributors across the whole release window

Use the release window, not just the strict tag delta for one repo. Include all
relevant repos covered by the public post.

Count human contributors from all of these evidence classes:

- commit authors and co-authors;
- merged PR authors;
- rejected, closed, or unmerged PR authors;
- PR reviewers and substantive commenters;
- issue authors/reporters, including rejected, closed, duplicate, not-planned, or
  not-implemented issues;
- substantive issue participants;
- maintainers who materially shaped scope, validation, or release decisions.

**Non-negotiable contributor rule:** a human's work does not need to ship to be a
release-window contribution. If they raised an issue or submitted a PR that was
part of the release window discussion, count them unless there is a specific
public-safety reason to exclude them. Do not silently narrow the list to merged
code.

Exclude AI/model/helper names from the public contributor field. They may appear
in validation/review prose only when useful and safe.

### 4. Draft with explicit contributor scope

The release entry should state what range was audited and what evidence classes
were used. Mention that closed/rejected/unmerged issues and PRs are included when
relevant. Keep the public contributor list human-only and source-supported.

For the current `lingtai-web`, fill the release-data shape rather than inventing
a Markdown article structure: localized title/summary, feature sections with
lead/bullets/why, contributors, validation, and links; then prepend the new
constant to `export const releases`.

Start from `assets/release-log-template.md`. It includes the canonical publish
destination, generated live URLs, required release-window statistics, collection
commands, and a `src/data/releases.ts` entry skeleton.

### 5. Build before pushing

Run the local site build and keep the log path or tail. Warnings such as known npm
audit advisories may be non-blocking, but report them honestly.

### 6. Publish through GitHub push and automatic deploy

After maintainer approval to publish, push the `lingtai-web` commit to GitHub.
For the current website, GitHub push to the deployment branch triggers automatic
site deployment. Do **not** treat failure of a local non-interactive
`wrangler deploy` (for example missing `CLOUDFLARE_API_TOKEN`) as a release
blocker. Local wrangler deploy is not the normal release path.

After pushing:

1. wait a short deployment window;
2. verify the expected live URLs;
3. send Jason both live URLs and GitHub source/commit links.

## Required release-window statistics

Every release log must include the window's measurable scope, not just prose
highlights. At minimum, publish:

- commit count per covered repo and combined total;
- merged PR count per covered repo and combined total;
- issue count per covered repo and combined total, with the query/window basis;
- files changed and `+insertions / -deletions` per covered repo and combined
  total;
- contributor evidence classes and validation gates.

If a number is not yet known, keep it as `TBD` in the draft and do not publish
until it is resolved or Jason explicitly accepts the omission.

## Validation

Before final report, verify:

- zh/en pages build successfully;
- contributor list includes humans from closed/rejected/unmerged PRs and issues;
- AI/model names are not in the public contributor field;
- the GitHub commit is pushed;
- live URLs resolve after automatic deploy, or any remaining deployment delay is
  reported as a live-site observation rather than a local-token blocker.

## Failure signals

- You used only commit authors or only merged PR authors.
- You excluded an issue/PR author because their item was rejected or not shipped.
- You presented a local `wrangler` token problem as the primary deployment blocker
  after the web commit was already pushed.
- You gave Jason a public URL without also checking the source commit or build.
- You wrote a standalone review artifact or `src/content/blog/release-day-*` post
  instead of following the website's canonical `/releases` archive structure.

## Submission record

- Originating correction: Jason H, Telegram, 2026-07-03.
- Submitted in: Lingtai-AI/lingtai-workflow PR for release blog publication workflow.
