---
name: workflow-template
description: >-
  Template for a user-submitted LingTai workflow or daemon tactic. Replace this
  frontmatter and body before submitting a real workflow.
version: 0.1.0
author: "<name or GitHub handle>"
tags:
  - workflow
  - advisory
last_verified: "YYYY-MM-DD"
advisory: true
---

# <Workflow name>

> Advisory only. This workflow is user-submitted and maintainer-reviewed, but it is not a system rule, model ranking, or default authorization.

## Use when

- <Situation where this workflow helps.>

## Avoid when / stop when

- <Situations where this workflow is unsafe, stale, too expensive, or not applicable.>

## Required evidence or benchmark case

- <What observation, artifact, or repeated success shows this workflow is useful?>

## Workflow

1. <Step one.>
2. <Step two.>
3. <Validation / review / human handoff.>

## Validation

- <Commands, checks, reviewer gates, or outcome criteria.>

## Failure signals

- <How to know this workflow is not working and should return to the parent/human.>

## Safety and privacy

- <Secrets, external side effects, user data, or permissions to watch.>

## Attribution

- Author: <name or GitHub handle>
- Submitted in: <PR or issue URL>
- Last verified: <date>
