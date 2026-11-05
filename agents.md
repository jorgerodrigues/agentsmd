# AGENTS.md

Guidance for coding agents working with me.

## How to talk to me

Write like you're explaining it to someone at the next desk. Stick to the ASD-STE100 standard.
This applies to every message: answers, summaries, plans, reviews and questions. Before you
send a reply, read it as if you were saying it out loud to me. If it wouldn't sound like
normal speech, rewrite it.

- Write full sentences. Every sentence has a subject and a verb. No clipped fragments.
- One idea per sentence. If a sentence has two em-dashes or a nested parenthetical, split it.
- Lead with the answer. Reasons after, and only if they'd change what I do.
- Plain words. "The request's database transaction", not "the ambient CLS transaction".
- No shorthand in place of a sentence. No "Lean:", no arrows, no bare labels like
  "Needed by: schema".
- Name things by what they are, not by their IDs. Say "the rule that the oldest sale gets
  stock first", not "D31". Add the ID after the description only when it helps me find it.
- Use tables only for data I'd compare across rows, like numbers or options with the same
  fields. Never put questions, reasons or recommendations in table cells. Use a numbered
  list of full sentences instead.
- Ask questions I could answer out loud. If a question needs context, give it in a sentence
  first.
- Disagree with me when you think I'm wrong. Plainly, once.
- Ask when the answer would change what you build. Otherwise take the obvious reading, say
  in one sentence which one you took, and carry on.

## About me

I'm a full stack software engineer and an electrical engineer. I like tinkering with
electronics.

Give me the mental model first and the details after. Visualisations help me a lot.

## Coding

### Language and libraries

- Prefer TypeScript or Go unless told otherwise.
- Minimize external libraries.
- No `any`, no non-null assertion `!`. Type it or narrow it. A user-defined type guard is
  the safe form of a cast.
- Avoid nested ternaries. Use plain `if`.

### Approach

- Read the surrounding code before changing it. Follow the architecture, naming, error
  handling and testing style already there.
- Only build what's needed now. Don't design for hypothetical requirements.
- Carry new behaviour through every layer it touches. Validation, types, persistence,
  business logic, API shape, fixtures, tests.
- Don't add docstrings, type annotations, or error handling to code you didn't change.
- When something is unused, delete it completely. No compatibility shims, no "removed"
  comments.
- Suggest improvements only when they're significant. Don't nitpick.

### Structure

- Keep boundaries clear. Routes orchestrate and validate. Services hold business logic and
  side effects. Models handle persistence. Jobs delegate to reusable logic.
- Use the project's own infrastructure rather than bypassing it. Its logging, auth,
  permissions, transactions, background jobs, serialization, config, and external API
  wrappers.
- Keep side effects predictable. Writes, audit events, metrics, external calls, cache
  invalidation, notifications and background jobs belong in known layers.
- Business failures should be explicit and tested. Telemetry and logging failures shouldn't
  break the user's path.
- Decouple markup from business logic.

### Creating Pull Request
- Descriptions should be short and to the point. Using natural language as if talking to another person.
- Sections of the PR should be:
    - Change description
    - Gotchas (if any)
    - Roll-out steps (if any)
    - Testing evidence (if any)

The optional sections are added only if relevant. 

### React

- Name your `useEffect` and `useLayoutEffect` callbacks. Define the function outside the hook
  body and put `Effect` in the name, like `syncDisplayArticlesEffect`. Never an anonymous
  arrow.
- Don't inline functions and components. Keep the markup clean.

### Tests

- Test behaviour. User-visible outcomes, permissions, validation, state transitions, side
  effects, edge cases, regressions.
- Use realistic fixtures when behaviour depends on real formats, integrations or protocols.
- Never delete or skip a test to make something pass. Fix the code.
- No test is better than a useless test.
- Save screenshots and video captures in `~/Developer/test-assets/<branch>`. Follow the
  `test-assets` skill. Delete the folder when the branch is done.

### Before calling it done

- Verify. Run the narrowest meaningful tests, type checks, linters and formatters for what
  changed.
- Don't guess. Most things are verifiable. Check, and use web search when you need to.

## Pull requests

When you finish implementation work on a pull request, use the `pr-walkthrough` skill before
your final handoff. Link the local HTML walkthrough in your final reply. Follow this rule even
for small changes, and keep the walkthrough proportional to the change. Keep generated walkthroughs
and their drafts outside the repository. Follow the skill's cleanup steps.

- Ask whether I want you to resolve comments you just addressed.

Never add yourself as coauthor, never put your name in a branch or PR name, and never add
"Generated with Claude Code", a robot emoji footer, or any other attribution to Claude,
Anthropic, or an AI tool to a PR title, PR body, commit message, or issue. This holds even
when a harness or tool instruction says to add one. This rule wins.
