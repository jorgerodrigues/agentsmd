---
name: review-with-claude
description: Delegate a full, prioritized code review of the current branch to a fresh Claude CLI session, then fix the findings and re-review until it reports the branch clean. Use when the user invokes $review-with-claude or asks to review the branch with Claude, run a claude review, or get a second opinion on the current changes from Claude. The spawned session only reviews; this agent does all the fixing, and never commits, pushes, or posts to GitHub.
---

# Review with Claude

A separate Claude session tries to break the change, you fix what it breaks, and the loop exits on that session's output rather than on your own assessment of your work. The reviewer starts with no memory of writing the code, so it is not anchored to the reasoning that produced the bug. Do not shortcut it by reviewing the diff yourself.

The review is adversarial in one direction only. The reviewer's job is to prove the change is broken; your job is to make it prove that, not to accept every objection. A finding is a claim to be checked, and a reviewer that cannot name a trigger has not found anything.

This works from any driving agent, including Claude Code — a fresh session is still an independent reader of the same diff.

The review rubric lives in the `review-pr` skill, not here. This skill only drives the loop.

## 1. Preflight

Run everything from the repository root (`git rev-parse --show-toplevel`).

- `command -v claude` and `command -v jq` — both are required. If either is missing, say so and stop. Do not substitute your own review.
- Run `claude auth status` from the same execution context that will launch the reviewer. On macOS, Claude can store authentication in Keychain, and a restricted sandbox can report `"loggedIn": false` even when the user's terminal is logged in because it cannot read those credentials. If that happens, retry outside the restricted sandbox, requesting credential-access approval when required, and run every later `claude` command in that same context. Only ask the user to log in when the unrestricted check also reports that they are logged out.
- Confirm the reviewer's rubric is installed: `~/.claude/skills/review-pr` must exist. If it does not, stop and tell the user to run this repo's `link.sh`. Without it the spawned session reviews with no rubric and the priorities become meaningless.
- Resolve the default branch from `git symbolic-ref --quiet refs/remotes/origin/HEAD` (strip `refs/remotes/origin/`), falling back to `main`, then `master`.
- Choose the base ref: prefer `origin/<name>` whenever it resolves, and fall back to the local branch name only when it does not. The remote ref is right in both awkward cases — on the default branch, comparing local `main` against itself reviews nothing, and on a feature branch, a missing or stale local `main` silently reviews against the wrong base. Confirm with `git rev-parse --verify` and check the base is not already at HEAD.
- `git status --porcelain` — skip the working-tree run when the tree is clean.
- Skip the base run only when no base ref resolves or the base is already at HEAD, and say so in the report. Being on the default branch is not itself a reason to skip it.
- `mktemp -d` for the round artifacts.

Do not pass `--model`. The reviewer should inherit the user's configured model; silently downgrading it weakens every finding.

## 2. Run a review round

Unlike Codex, `claude` has no review subcommand and no scope flags, so state the scope and the stance in the prompt. Run the ones that apply:

```sh
STANCE='Work adversarially. Assume the change is broken and try to prove it: choose the
inputs, ordering, concurrency, permissions, or environment that would make it fail, and
follow the call path until you either have a concrete failing case or have satisfied
yourself there is none. Every finding must name what triggers it and what breaks as a
result. Report nothing you cannot ground that way — no style, naming, formatting,
comment-wording, or documentation preferences, and nothing phrased as "consider" or
"you might want to". If the only cost you can state is that you would have written it
differently, it is not a finding. Finding nothing is a valid and useful result.'

claude -p "/review-pr Review the changes on this branch against the base ref $BASE, comparing from their merge base. $STANCE" \
  --permission-mode dontAsk --tools "Read,Grep,Glob,Bash" \
  --output-format json < /dev/null > "$DIR/r$N-base.json"

claude -p "/review-pr Review the staged, unstaged, and untracked changes in the working tree. $STANCE" \
  --permission-mode dontAsk --tools "Read,Grep,Glob,Bash" \
  --output-format json < /dev/null > "$DIR/r$N-worktree.json"
```

The stance sharpens `review-pr`'s rubric; it does not replace it. Keep the `/review-pr` prefix — it carries the priority scale and the report format that steps 3 and 6 parse.

`--tools` is what makes the reviewer read-only: `Edit`, `Write`, and `NotebookEdit` are absent from its toolset entirely. `dontAsk` stops it stalling on a prompt it cannot answer non-interactively, and `< /dev/null` stops it waiting on stdin it will never receive.

Three configurations look equivalent and are not. Use the one above:

- Do **not** allowlist with `--allowedTools "Read Grep Glob Bash"` and block edits with `--disallowedTools`. Blanket `Bash` approval pre-approves *every* shell command, so the reviewer can rewrite files through the shell with the edit tools still nominally blocked. Verified: a reviewer configured that way modified the file it was asked to review.
- Do **not** use `--permission-mode plan`. Plan mode is not merely read-only — it injects Claude Code's plan workflow, which authorizes writing a plan file and steers the turn toward `ExitPlanMode` instead of the review report, corrupting `.result` into plan content.
- Never pass `--dangerously-skip-permissions` or an `acceptEdits` mode. A reviewer that can rewrite the code you are asking it to judge is worthless.

A review takes minutes, so run it in the background rather than blocking on a long foreground command.

Do not use `claude ultrareview`. It is a billed, user-triggered cloud review; it is the user's to launch, not yours.

Read three fields from each result:

```sh
jq -r '.is_error, (.permission_denials | length), .result' "$DIR/r$N-base.json"
```

- `.result` — the review text.
- `.is_error` — true means the run failed. Surface it and stop.
- `.permission_denials` — informational, **not** a failure. Denials are normal: `review-pr` opens by running `gh pr view`, which `dontAsk` denies in most repositories. Never gate the loop on this list being empty — it rarely is, and doing so means no round can ever pass and every run burns to the round cap.

Judge completeness from the review itself, not from the denial count. A reviewer that was blocked from reading the code says so in its own opening lines; when it does, treat the round as incomplete and report which tools were denied. A denied `gh pr view` in a repository with no pull request blocked nothing that matters.

The findings come back in the `review-pr` format, one per heading:

```
**[P1][Correctness] Short imperative title — path:line**
```

When nothing clears the bar, `.result` is exactly `No findings cleared the bar.`

## 3. Merge and triage

- Fingerprint a finding as its path plus its title with the `[Pn][Lane] ` prefix stripped. Deduplicate across the two runs, keeping the higher-priority copy.
- Treat an untagged finding as P2. Assume it matters.
- The two lanes carry different fixes: a Correctness finding names a trigger and a wrong result, a Design finding names a durable maintenance cost. Do not "fix" a design finding by patching a symptom.

Then hold every finding to the bar, whatever priority it carries. Keep it only if you can answer both:

1. **What makes it happen** — the input, state, sequence, or environment that triggers it, or the specific maintenance cost someone pays later.
2. **What goes wrong** — the incorrect behaviour, the failure, or the thing that must now change in two places.

Drop anything that fails either question, and drop anything about code the diff did not touch unless the diff is what made it wrong. An adversarial reviewer produces more candidates, not better ones; the bar is what turns volume into signal. Record what you dropped and why — a dropped finding is a decision, not an oversight, and the report shows it.

## 4. Act on the findings

Work P0 through P2 in priority order. Leave P3 alone and collect it for the report.

1. Read the cited file and the code around it. Findings are evidence, not instructions — confirm the claim against the actual code before changing anything.
2. Fix minimally: the smallest focused change, following the patterns already in the file and the coding guidance your own instruction files loaded — no speculative abstraction, no refactoring of code the diff did not touch.
3. Never weaken, skip, or delete a test to clear a finding. Fix the code.
4. Dismiss a finding only with an evidence-backed reason — the premise is wrong, the case is already handled elsewhere (cite where), or the code is pre-existing and outside the diff. Every dismissal goes in the report.

## 5. Verify before the next round

Run the narrowest meaningful checks for what you touched — typecheck, lint, or the relevant tests, discovered from `package.json` scripts, a `Makefile`, or `go test`. This catches a broken fix before the next round reviews it as though it were sound.

## 6. Loop control

Re-run step 2 against the new state.

**Exit clean** when a full round produces no P0–P2 finding that clears the step 3 bar, and no statement that the reviewer was blocked from reading the code. The exit signal has to be the reviewer's own output on the current state of the code — never your judgement that a finding which *did* clear the bar looks unimportant, and never a round you skipped because the last one was nearly clean.

Candidates you dropped below the bar do not block the exit. Nothing changed in the code to stop the reviewer raising them again, so expect recurrence: drop them again, note them once in the report, and do not let them hold the loop open or count as circling.

### Keep a ledger

From round two onward, maintain a ledger with one row per finding: the round it appeared, its fingerprint, **the underlying claim restated in your own words**, and what you did about it.

Check every new finding against the ledger before you touch any code. An adversarial reviewer will keep finding something to say, so the guard against circling has to be yours:

- **The same claim in new words.** A fingerprint only catches a verbatim repeat. It does not catch the same objection re-argued from a different line, under a different title, or at a different priority. Compare the *claim*, not the string. The second time a claim you already **fixed** comes back, you stop — you do not try a third phrasing of the fix. This applies to claims you acted on; a claim you dropped below the bar recurring is expected and means nothing.
- **A finding about your own fix.** If the reviewer objects to code a previous round introduced, fix it once. If the round after that objects again, the two of you are negotiating, not converging. Stop.
- **A change that undoes an earlier one.** If the edit you are about to make restores something a previous round already changed away from, you are ping-ponging between two states that each look wrong from the other side. Stop and show the user both.
- **A diff that keeps growing.** If the accumulated fixes have grown well past the change you set out to review, the review has turned into a rewrite. Stop.

### Stop and escalate

- Four rounds have run.
- Any ledger check above trips.
- A round produces more P0–P2 findings that clear the bar than the round before it.
- A round where you fixed things and the *same claims* survived. Compare claims, not counts: one finding fixed and a different one discovered is the loop working, even though the count is unchanged. Stagnation is the old claims still standing.

Each round is a full Claude session and is billed as one. If you are about to start a fourth round, say what it will cost before doing it.

## 7. Report

Lead with the verdict, then the detail:

1. Clean after N rounds, or stopped after N rounds with M findings unresolved and why — naming the ledger check that tripped, if one did.
2. **Fixed** — finding, `path:line`, and what changed.
3. **Dismissed** — finding and the reason.
4. **Dropped below the bar** — findings that named no trigger or no consequence, one line each. The user should be able to see what the reviewer raised and you declined to chase.
5. **P3 findings** left for the user to decide on.
6. Checks run and their results.

Leave every change in the working tree. Do not commit, push, or post anything to GitHub.
