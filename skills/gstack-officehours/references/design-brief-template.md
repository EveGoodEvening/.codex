# Design Brief Template

Keep the brief concise unless the user asks for more depth. A good default is 400-900 words.

Do not invent evidence, numbers, users, or constraints. If something is unknown, label it as an assumption or open question.

If the brief is saved to a file, you may add lightweight metadata near the top:

- `Generated: {date}`
- `Mode: Startup` or `Mode: Builder`
- `Status: DRAFT` or `Status: APPROVED`
- `Supersedes: {prior brief path}` when revising an earlier repo-local brief

## Startup Brief

```markdown
# Design Brief: {title}

## Problem Statement
{What problem exists, for whom, and why it matters now}

## Demand Evidence
{Observed behavior, direct quotes, payments, urgency, repeated usage, or lack thereof}

## Status Quo
{How the user solves it today, including manual workarounds and their cost}

## Target User And Wedge
{The specific person and the smallest sellable version}

## Constraints
{Timeline, integrations, repo constraints, business constraints, or why the scope must stay narrow}

## Premises
- {premise 1}
- {premise 2}
- {premise 3}

## Landscape Notes
{Optional. Include only when live browsing or external source review materially changed the recommendation}

## Approaches Considered
{Include at least 2 materially different approaches. One must be the minimal viable path. One must be the stronger long-term path. Add a third only when a lateral option genuinely reframes the problem.}

### Approach A: {minimal viable path}
{Summary, pros, cons, effort, risk}

### Approach B: {stronger long-term path}
{Summary, pros, cons, effort, risk}

### Approach C: {optional lateral path}
{Use only when it is materially different}

## Recommended Approach
{Which path to choose and why}

## Open Questions
- {unknown 1}
- {unknown 2}

## Success Criteria
- {measurable sign 1}
- {measurable sign 2}

## Distribution Plan
{Optional. Include when the artifact needs a clear path to users such as package distribution, releases, or demo access}

## Next Real-World Action
{The next conversation, observation, sale, pilot, or prototype move}
```

## Builder Brief

```markdown
# Design Brief: {title}

## Problem Statement
{What is being built, for whom, and what makes it worth doing}

## What Makes This Exciting
{The delight, novelty, or "whoa" factor}

## Constraints
{Time, tools, skills, integrations, design limits}

## Premises
- {premise 1}
- {premise 2}
- {premise 3}

## Landscape Notes
{Optional. Include only when external review changed the design direction or differentiated the concept}

## Approaches Considered
{Include at least 2 materially different approaches. One must be the minimal viable path. One must be the stronger long-term path. Add a third only when a lateral option genuinely reframes the problem.}

### Approach A: {minimal viable path}
{Summary, pros, cons, effort, risk}

### Approach B: {stronger long-term path}
{Summary, pros, cons, effort, risk}

### Approach C: {optional lateral path}
{Use only when it is materially different}

## Recommended Approach
{Which path to choose and why}

## Open Questions
- {unknown 1}
- {unknown 2}

## Success Criteria
- {what "done" looks like}
- {what makes it demo-worthy or useful}

## Distribution Plan
{Optional. How people will discover, access, or try it if that matters}

## Next Real-World Action
{The very next action to take. Make it concrete. It can be a conversation, observation, demo, or thin-slice build step, but not "go build it."}

## Next Build Steps
1. {step 1}
2. {step 2}
3. {step 3}
```

## Delivery Rules

- Lead with the recommendation, then show the alternatives.
- Quote the user's own evidence or wording where it sharpens the brief.
- Prefer plain language over strategy jargon.
- Every brief must include at least 2 approaches: one minimal viable path and one stronger long-term path. A lateral third path is optional.
- Every brief must end with one concrete next action or assignment. Do not end with "go build it."
- If the user asked to save the brief, write it into an obvious repo-local path instead of a hidden global directory.
- Support a handoff loop:
  - Approve: mark saved briefs as `Status: APPROVED`
  - Revise: update the same brief in place when practical
  - Start over: resume questioning instead of defending a weak recommendation
