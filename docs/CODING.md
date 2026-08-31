# Coding

## Language and libraries

- Prefer TypeScript or Go unless told otherwise.
- Minimize external libraries.
- No `any`, no non-null assertion `!`. Type it or narrow it — a user-defined type guard is the
  safe form of a cast.
- Avoid nested ternaries. Use plain `if`.

## Approach

- Read the surrounding code before changing it, and follow the architecture, naming, error
  handling and testing style already there.
- Only build what's needed now. Don't design for hypothetical requirements.
- Make minimal, focused changes. Don't refactor or "improve" surrounding code unless asked.
- Prefer editing an existing file to creating a new one, and extending an existing path to
  creating a parallel one: a new case, option, adapter, handler, or schema field before a new
  surface area.
- Make complete vertical changes. Carry new behaviour through every layer it touches —
  validation, types, persistence, business logic, API shape, fixtures, tests.
- Don't add boilerplate docstrings, type annotations, or error handling to code you didn't change.
- When something is unused, delete it completely. No compatibility shims, no "removed" comments.
- Suggest improvements only when they are significant. Don't nitpick.

## Structure

- Keep boundaries clear: routes orchestrate and validate, services hold business logic and side
  effects, models handle persistence, jobs delegate to reusable logic.
- Use the project's own infrastructure rather than bypassing it — its logging, auth, permissions,
  transactions, background jobs, serialization, config, and external API wrappers.
- Extract a helper when the same small job repeats or a block runs more than a couple of lines,
  and let it do one obvious thing. Don't stack normalize/parse/validate layers or wrappers that
  restate a one-liner.
- Keep side effects predictable: writes, audit events, metrics, external calls, cache
  invalidation, notifications and background jobs belong in known layers.
- Business failures should be explicit and tested. Telemetry and logging failures shouldn't break
  the user's path.
- Decouple markup from business logic.

## React

- Use named `useEffect`/`useLayoutEffect` callbacks: define the function outside the hook body and
  put `Effect` in the name (`syncDisplayArticlesEffect`). Never an anonymous arrow.
- Avoid inlining functions and components. Keep the markup clean.

## Tests

- Test behaviour: user-visible outcomes, permissions, validation, state transitions, side effects,
  edge cases, regressions.
- Use realistic fixtures when behaviour depends on real formats, integrations or protocols.
- Never delete or skip a test to make something pass. Fix the code.

## Pull requests

- Never answer GitHub comments.
- Ask whether I want you to resolve comments you just addressed.

## Before calling it done

- Verify. Run the narrowest meaningful tests, type checks, linters and formatters for what changed.
- Don't guess. Most things are verifiable — check, and use web search when you need to.
