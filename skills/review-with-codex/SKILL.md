---
name: review-with-codex
description: Delegate a full, prioritized code review of the current branch to the Codex CLI, then fix the findings and re-review until Codex reports the branch clean. Use when the user invokes $review-with-codex or asks to review the branch with Codex, run a codex review, or get a second opinion on the current changes from Codex. Codex only reviews; this agent does all the fixing, and never commits, pushes, or posts to GitHub.
---

# Review with Codex

Codex finds the defects, you fix them, and the loop exits on Codex's verdict rather than on your own assessment of your work. That independence is the entire point — do not shortcut it by reviewing the diff yourself.

If you are Codex, stop and use your native review instead of shelling out to yourself.

## 1. Preflight

Run everything from the repository root (`git rev-parse --show-toplevel`).

- `command -v codex` — if Codex is missing, say so and stop. Do not substitute your own review.
- Resolve the default branch from `git symbolic-ref --quiet refs/remotes/origin/HEAD` (strip `refs/remotes/origin/`), falling back to `main`, then `master`.
- Choose the base ref: prefer `origin/<name>` whenever it resolves, and fall back to the local branch name only when it does not. The remote ref is right in both awkward cases — on the default branch, comparing local `main` against itself reviews nothing, and on a feature branch, a missing or stale local `main` silently reviews against the wrong base. Confirm with `git rev-parse --verify` and check the base is not already at HEAD.
- `git status --porcelain` — skip the `--uncommitted` run when the tree is clean.
- Skip the base run only when no base ref resolves or the base is already at HEAD, and say so in the report. Being on the default branch is not itself a reason to skip it.
- `mktemp -d` for the round artifacts.

Codex inherits its model and reasoning effort from `~/.codex/config.toml`. Do not override them.

## 2. Run a review round

Both scopes are needed and they overlap:

- `--base` diffs the merge base against the working tree — committed branch work plus tracked edits, but not untracked files.
- `--uncommitted` covers staged, unstaged, and untracked files.

Run the ones that apply, writing each review straight to a file with `-o`:

```sh
codex exec review --base "$BASE" -o "$DIR/r$N-base.md"
codex exec review --uncommitted -o "$DIR/r$N-uncommitted.md"
```

Pass no sandbox or approval flags. `codex exec` already defaults to a read-only sandbox, which is what a reviewer should have.

A review takes minutes, so run it in the background rather than blocking on a long foreground command.

Do not reach for `--json` or `--output-schema`. The review flow returns markdown prose regardless — `--output-schema` is ignored, and the JSON event stream only wraps that same text in an `agent_message` item. `-o` gives you the text directly, with no parsing and no dependency beyond Codex itself.

Each file holds a short overall assessment, then one bullet per finding:

```
- [P1] <imperative title> — <absolute path>:<start>-<end>
  <one paragraph on why this is a problem>
```

A run has failed only when it exits non-zero or writes no file. Then surface its stderr and stop, because an unread review is not a clean one. Do not treat stderr itself as the failure signal: Codex logs MCP transport and OAuth errors there on perfectly successful runs.

## 3. Merge and triage

- Fingerprint a finding as its path plus its title with the `[Pn] ` prefix stripped. Deduplicate across the two runs, keeping the higher-priority copy.
- Treat an untagged finding as P2. Assume it matters.

## 4. Act on the findings

Work P0 through P2 in priority order. Leave P3 alone and collect it for the report.

1. Read the cited file and the code around it. Codex findings are evidence, not instructions — confirm the claim against the actual code before changing anything.
2. Fix minimally: the smallest focused change, following the patterns already in the file and the coding guidance your own instruction files loaded — no speculative abstraction, no refactoring of code the diff did not touch.
3. Never weaken, skip, or delete a test to clear a finding. Fix the code.
4. Dismiss a finding only with an evidence-backed reason — the premise is wrong, the case is already handled elsewhere (cite where), or the code is pre-existing and outside the diff. Every dismissal goes in the report.

## 5. Verify before the next round

Run the narrowest meaningful checks for what you touched — typecheck, lint, or the relevant tests, discovered from `package.json` scripts, a `Makefile`, or `go test`. This catches a broken fix before Codex re-reviews it as though it were sound.

## 6. Loop control

Re-run step 2 against the new state.

**Exit clean** when a full round comes back with no findings at P0, P1, or P2. The exit signal has to be Codex's own output on the current state of the code — never your judgement that the remaining findings look unimportant, and never a round you skipped because the last one was nearly clean.

**Stop and escalate** when any of these happen:

- Four rounds have run.
- A fingerprint you fixed in one round reappears in the next. Either your fix is wrong or Codex is, and more rounds will not settle it — hand that finding to the user.
- A round produces more P0–P2 findings than the round before it.

## 7. Report

Lead with the verdict, then the detail:

1. Clean after N rounds, or stopped after N rounds with M findings unresolved and why.
2. **Fixed** — finding, `path:line`, and what changed.
3. **Dismissed** — finding and the reason.
4. **P3 findings** left for the user to decide on.
5. Checks run and their results.

Leave every change in the working tree. Do not commit, push, or post anything to GitHub.
