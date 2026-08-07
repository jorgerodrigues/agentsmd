---
name: review-with-codex
description: Delegate a full, prioritized code review of the current branch to the Codex CLI, then fix the findings and re-review until Codex reports the branch clean. Use when the user invokes $review-with-codex or asks to review the branch with Codex, run a codex review, or get a second opinion on the current changes from Codex. Codex only reviews; this agent does all the fixing, and never commits, pushes, or posts to GitHub.
---

# Review with Codex

Codex tries to break the change, you fix what it breaks, and the loop exits on Codex's output rather than on your own assessment of your work. That independence is the entire point — do not shortcut it by reviewing the diff yourself.

The review is adversarial in one direction only. Codex's job is to prove the change is broken; your job is to make it prove that, not to accept every objection. A finding is a claim to be checked, and a reviewer that cannot name a trigger has not found anything.

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

`codex exec review` takes **either** a scope flag **or** a custom prompt, never both — `--uncommitted` with a prompt fails outright with `the argument '--uncommitted' cannot be used with '[PROMPT]'`. Since the stance has to be stated, use the prompt form and describe the scope in it, the way Codex's own built-in templates do.

```sh
STANCE='Work adversarially. Assume the change is broken and try to prove it: choose the
inputs, ordering, concurrency, permissions, or environment that would make it fail, and
follow the call path until you either have a concrete failing case or have satisfied
yourself there is none. Every finding must name what triggers it and what breaks as a
result. Report nothing you cannot ground that way — no style, naming, formatting,
comment-wording, or documentation preferences, and nothing phrased as "consider" or
"you might want to". If the only cost you can state is that you would have written it
differently, it is not a finding. Finding nothing is a valid and useful result.'

codex exec review "Review the code changes against the base branch $BASE. Find the merge
base with \`git merge-base HEAD $BASE\`, then diff against that SHA. $STANCE" \
  -o "$DIR/r$N-base.md"

codex exec review "Review the staged, unstaged, and untracked changes in the working
tree. $STANCE" -o "$DIR/r$N-uncommitted.md"
```

The prompt form keeps Codex's `[Pn]` priority tagging — that comes from its review mode, not from the scope flag — so steps 3 and 6 parse the same output as before. Verified: the prompt form scoped correctly to the working tree and still tagged priorities.

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

Then hold every finding to the bar, whatever priority it carries. Keep it only if you can answer both:

1. **What makes it happen** — the input, state, sequence, or environment that triggers it, or the specific maintenance cost someone pays later.
2. **What goes wrong** — the incorrect behaviour, the failure, or the thing that must now change in two places.

Drop anything that fails either question, and drop anything about code the diff did not touch unless the diff is what made it wrong. An adversarial reviewer produces more candidates, not better ones; the bar is what turns volume into signal. Record what you dropped and why — a dropped finding is a decision, not an oversight, and the report shows it.

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

**Exit clean** when a full round produces no P0–P2 finding that clears the step 3 bar. The exit signal has to be Codex's own output on the current state of the code — never your judgement that a finding which *did* clear the bar looks unimportant, and never a round you skipped because the last one was nearly clean.

Candidates you dropped below the bar do not block the exit. Nothing changed in the code to stop Codex raising them again, so expect recurrence: drop them again, note them once in the report, and do not let them hold the loop open or count as circling.

### Keep a ledger

From round two onward, maintain a ledger with one row per finding: the round it appeared, its fingerprint, **the underlying claim restated in your own words**, and what you did about it.

Check every new finding against the ledger before you touch any code. An adversarial reviewer will keep finding something to say, so the guard against circling has to be yours:

- **The same claim in new words.** A fingerprint only catches a verbatim repeat. It does not catch the same objection re-argued from a different line, under a different title, or at a different priority. Compare the *claim*, not the string. The second time a claim you already **fixed** comes back, you stop — you do not try a third phrasing of the fix. This applies to claims you acted on; a claim you dropped below the bar recurring is expected and means nothing.
- **A finding about your own fix.** If Codex objects to code a previous round introduced, fix it once. If the round after that objects again, the two of you are negotiating, not converging. Stop.
- **A change that undoes an earlier one.** If the edit you are about to make restores something a previous round already changed away from, you are ping-ponging between two states that each look wrong from the other side. Stop and show the user both.
- **A diff that keeps growing.** If the accumulated fixes have grown well past the change you set out to review, the review has turned into a rewrite. Stop.

### Stop and escalate

- Four rounds have run.
- Any ledger check above trips.
- A round produces more P0–P2 findings that clear the bar than the round before it.
- A round where you fixed things and the *same claims* survived. Compare claims, not counts: one finding fixed and a different one discovered is the loop working, even though the count is unchanged. Stagnation is the old claims still standing.

## 7. Report

Lead with the verdict, then the detail:

1. Clean after N rounds, or stopped after N rounds with M findings unresolved and why — naming the ledger check that tripped, if one did.
2. **Fixed** — finding, `path:line`, and what changed.
3. **Dismissed** — finding and the reason.
4. **Dropped below the bar** — findings that named no trigger or no consequence, one line each. The user should be able to see what the reviewer raised and you declined to chase.
5. **P3 findings** left for the user to decide on.
6. Checks run and their results.

Leave every change in the working tree. Do not commit, push, or post anything to GitHub.
