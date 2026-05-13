---
name: gen-todolist
description: Turn a resolved task or planning topic into a detailed Markdown todo checklist and planning document, optionally writing it to a specified file. Use when Codex should not implement yet and instead produce a structured checklist, milestone list, or execution tracker without adding open questions, especially requests like "先整理详细 todolist/checklist" or "把计划写到某个文档里".
---

# Generate Todo List

Turn a resolved task into a detailed Markdown checklist and planning note. Focus on producing a usable execution tracker rather than prose-heavy analysis.

The default output should not contain open questions. If material missing information prevents an actionable checklist, ask for clarification before writing or updating the checklist.

## Workflow

1. Determine whether the request names a planning topic, an output document path, or both.
2. If a target document exists, read it first and preserve useful structure or completed items unless the user asks for a rewrite.
3. Review the relevant code, design notes, or requirements so the checklist reflects the actual work.
4. If a source plan contains unresolved open questions, stop and ask the user to resolve them before generating the checklist unless the user explicitly asks to preserve unresolved questions.
5. If the user has approved a plan, treat it as the resolved source of truth. Do not invent new open questions during conversion.
6. If material missing information still blocks an actionable checklist, ask focused follow-up questions before writing the checklist.
7. Break the work into phases or workstreams and write actionable checklist items using Markdown checkboxes.
8. Include validation tasks, dependencies, blockers, decisions, and assumptions.
9. Mark items as completed only when there is direct evidence they are already done.
10. If the user specifies a destination file, write or update that document. Otherwise, return the checklist inline.

## Output Expectations

- Prefer short, executable checklist items over long narrative paragraphs.
- Use clear Markdown sections such as `Goal`, `Context / Assumptions`, `Decisions`, `Checklist`, `Validation`, and `Dependencies` when helpful.
- Do not include an `Open Questions` section by default. Only include one when the user explicitly requests unresolved questions to be recorded.
- Group related work so the list can be used as a progress tracker.
- Include file references, commands, or test targets when they make the checklist more concrete.
- Keep unfinished work as `[ ]`. Use `[x]` only for confirmed completed steps.

## Guardrails

- Do not start implementing code unless the user explicitly switches from planning to execution.
- Do not mark speculative or future steps as complete.
- Do not use the todo document as a place to defer clarification that should happen before planning.
- Do not overwrite an existing planning document blindly; preserve signal and clean up only when the user asks for replacement.
- Keep the document concise enough to stay maintainable during execution.
