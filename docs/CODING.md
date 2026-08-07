# General

When writing code:
1. Minimize the use of external libraries
2. Prefer typescript or golang unless instructed otherwise
3. Always use the very best practices for production code
4. Start with the simplest implementation but provide more advanced options.


## Code Style

- Write simple, readable code. Avoid unnecessary abstractions and over-engineering. Do not over-engineer.
- Only build what's needed now — don't design for hypothetical future requirements.
- Use clear, descriptive names. If the code is self-explanatory, skip the comment.
- Understand the codebase patterns and follow them.
- Prefer editing existing files over creating new ones.

## Important
- NEVER answer github comments.
- ASK whether the user wants you to resolve comments which you just addressed.
- NEVER add yourself as co-author or mention it.
- ALWAYS verify your work before calling it done.
- DO NOT guess. Most information is verifiable, so please check. Use web search whenever you need.
- You are encouraged to use the `fallow` cli in order to check for dead code or other issues.
- REACT: avoid inlining functions and components as much as it is reasonable. The markup should be kept as clean as possible
- REACT: use named `useEffect`/`useLayoutEffect` callbacks — define the effect function outside the hook body and include `Effect` in the name (e.g. `syncDisplayArticlesEffect`); never use anonymous arrow functions
- Avoid inlining! Instead write functions, components, hooks as much as possible  
- Prefer simple named helpers over ceremony or long inlines. Extract a function when the same small job repeats or a block is more than a couple of lines — but the helper should do one obvious thing (e.g. trim an optional string to `null`). Don't stack normalize/parse/validate layers, sentinel `undefined` vs `null` schemes, or extra wrappers that only restate a one-liner.

## Approach

- Always read relevant code before modifying it.
- Make minimal, focused changes — don't refactor or "improve" surrounding code unless asked.
- Don't add boilerplate docstrings, type annotations, or error handling to code you didn't change.
- When something is unused, delete it completely — no compatibility shims or "removed" comments.
- Never delete or skip tests to make something work. Fix the code, not the tests.
- Suggest improvements only when they are significant. Don't nitpick small things.
- When in doubt, ask instead of assuming.
- Be very critical with yourself - never add more code than what is absolutely needed - Imagine that you will be reviewed by Linus Torvalds himself. 
- ALWAYS ask and clarify when the situation is ambiguous and/or the requirements are not clear. Never build on assumptions alone.

## General Coding Practices

- Read the surrounding code before changing it. Follow the project's existing architecture, naming, error handling, and testing style.
- Prefer extending an existing path over creating a parallel one. Add a case, option, adapter, handler, schema field, or branch before inventing a new surface area.
- Make complete vertical changes. Carry new behavior through every layer it actually touches: validation, types, persistence, business logic, UI/API shape, documentation, fixtures, and tests.
- Keep boundaries clear. Controllers/routes should orchestrate and validate; services should hold business logic and side effects; models/repositories should handle persistence; jobs/workers should delegate to reusable logic.
- Use the project's infrastructure instead of bypassing it. Reuse established wrappers for logging, auth, permissions, transactions, background jobs, serialization, configuration, external APIs, and observability.
- Avoid speculative abstractions. Extract helpers only when they reduce real duplication, clarify a domain rule, or match an established local pattern.
- Keep domain code strongly typed and explicit. Avoid broad casts, unchecked null assumptions, stringly typed state, and catch-all data shapes unless they are isolated at a true boundary.
- Treat side effects deliberately. Keep writes, audit events, metrics, external calls, cache invalidation, notifications, and background jobs in predictable layers.
- Fail intentionally. Business failures should be explicit and tested; non-critical telemetry/logging failures should not break the main user path unless the product requires it.
- Encode important domain rules in named functions and tests. Comments should explain standards, invariants, or surprising constraints, not restate obvious code.
- Decouple markup and business logic
- Avoid nested ternaries or the likes. Use simple `if` statements instead.

In short: read first. Extend existing paths. Make complete vertical changes. Respect boundaries. Use project infrastructure. Stay explicit. Test behavior. Delete dead code. Verify.

## Tests
- Write behavior-focused tests. Cover user-visible behavior, permissions, validation, state transitions, side effects, edge cases, and regressions.
- Use realistic fixtures when behavior depends on real-world formats, integrations, protocols, or standards.
- Delete unused code completely. Do not leave compatibility shims, dead branches, TODO scaffolding, or "temporary" fallbacks without a clear need.
- Verify before calling work done. Run the narrowest meaningful tests, type checks, linters, or formatters for the area changed.

