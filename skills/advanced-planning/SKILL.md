---
name: advanced-planning
description: Perform interactive project-manager style planning for a requested change without writing code. Use when Codex should restate requirements, inspect the codebase, resolve material unknowns through discussion, compare approaches, analyze tradeoffs, and recommend a final plan with no remaining open questions, especially requests like "先不要写代码，先分析方案并给出最佳计划".
---

# Advanced Planning

Produce a structured analysis before implementation. Think like an experienced project manager: clarify the real problem, resolve material unknowns through discussion, compare viable solutions, and recommend the best path with explicit tradeoffs.

A material open question is missing information that could change scope, architecture, sequencing, dependencies, or the recommended approach. Material open questions must be resolved before delivering a final plan.

## Workflow

1. Restate the user's request and identify goals, constraints, and success criteria.
2. Inspect the relevant code, architecture, configs, and existing conventions before proposing solutions.
3. Identify material unknowns before recommending a final plan.
4. If material unknowns exist, enter a clarification loop:
   - Ask focused follow-up questions before producing the final plan.
   - Prefer 1-3 questions at a time, and explain briefly why each answer affects the plan.
   - After the user answers, incorporate the answers and check again for remaining material unknowns.
   - Continue until there are no material open questions.
5. If the user explicitly asks to proceed without answering, choose conservative assumptions, label them as assumptions, and do not present them as open questions.
6. Explore the most viable implementation options, prioritizing mature ecosystem solutions and patterns already used in the repository.
7. Compare the options with concrete pros, cons, fit, engineering cost, operational risk, and maintenance burden.
8. Call out environment concerns early, including dependency versions, compatibility issues, migration concerns, or operational prerequisites.
9. Recommend the best option, explain why it wins, and outline how it could evolve later.
10. Deliver a phased execution plan with validation work and rollout concerns.

## Output Expectations

- Keep the response in planning mode. Do not write code.
- While clarifying, keep responses short and centered on the questions that unblock the plan.
- For the final plan, prefer a structure such as `Problem`, `Current State`, `Resolved Requirements`, `Options`, `Recommendation`, `Execution Plan`, `Validation`, and `Risks`.
- Do not include an `Open Questions` section in a final plan unless the user explicitly asks for one.
- If the user asks to dump or write the final plan to Markdown and material questions remain, pause and ask the remaining questions instead of writing a document with open questions.
- Compare more than one approach when a real choice exists. Do not fabricate alternatives just to satisfy the format.
- Make tradeoffs explicit: complexity, delivery speed, maintainability, and scalability.
- Favor proven tools and stable approaches over custom reinvention unless the repository clearly requires something else.

## Guardrails

- Do not skip codebase inspection and jump straight to abstract solutioning.
- Do not present a plan as final while material open questions remain.
- Do not hide uncertainty while clarifying. In the final plan, record only resolved assumptions, explicit decisions, and known risks.
- Do not invent new open questions when converting an already-approved plan into Markdown or a todo list. Preserve resolved decisions and assumptions as the source of truth.
- Do not recommend a technically elegant option if it is misaligned with the codebase, team constraints, or operating environment.
- Keep the recommendation decisive when the evidence points to a clear best path.
