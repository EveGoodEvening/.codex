---
name: simple-planning
description: Read and understand a codebase, then produce a detailed implementation plan without writing code. Use when Codex should inspect relevant files first and respond with a scoped plan for a feature, bug fix, refactor, or investigation, especially requests like "先别实现，先给我一个详细计划", "read the codebase and plan X", or "no need to start implementing yet".
---

# Simple Planning

Produce a practical plan after reading the relevant parts of the repository. Stay in planning mode unless the user explicitly asks you to write the plan into a document.

## Workflow

1. Read the files, configs, tests, and entry points needed to understand the request.
2. Restate the task in your own words and summarize the current behavior or structure you found.
3. Identify the components, modules, or files that would likely be affected.
4. Produce an ordered implementation plan that is specific enough for another engineer to execute.
5. Call out assumptions, dependencies, blockers, and any missing information that could change the plan.
6. Include validation work such as tests to run, edge cases to check, and rollout or migration steps when relevant.

## Output Expectations

- Keep the response planning-focused. Do not start implementing.
- Prefer concrete file or module references over abstract advice.
- Make the plan actionable and ordered from discovery to validation.
- If the request is underspecified, ask only the minimum necessary questions and otherwise proceed with explicit assumptions.
- If multiple approaches exist but one clearly matches the codebase, recommend it briefly instead of turning the answer into a long comparison.

## Guardrails

- Avoid generic project-management filler.
- Avoid inventing architecture that is not supported by the repository.
- When evidence is missing, say so directly.
- Anchor the plan to existing patterns in the codebase whenever possible.
