---
name: babysit-pr
description: Watch an open pull request through to green and mergeable — address review comments, rebase past merge conflicts, push the fix, resolve the bot threads it settles, wait for CI, and fix whatever failed, round after round. Use when the user invokes $babysit-pr or asks to babysit a PR, handle PR comments, fix failing CI or a merge conflict, keep working a PR until the checks pass, or respond to review feedback on the current branch. The only reply it ever posts is a brief note on feedback it declines; everything else it answers with code.
---

# Babysit a pull request

Drive an open PR to the point where CI is green, the branch merges cleanly, and nothing actionable is left open. Each round: read the feedback and the state of the PR, fix what deserves fixing, rebase if the base moved under you, push, resolve the bot threads you settled, then wait for CI and start again.

Review comments and CI failures are the same job here. A failing test, a coverage drop, and a conflict with the base all block the merge exactly as a reviewer's objection does, and each one has a right fix and a tempting shortcut that makes the check go green without making the code correct. The shortcuts are named as you go; do not take them.

Two rules hold for the whole run:

- **The only reply you ever write is a decline.** When you decide not to act on a piece of feedback, post one brief comment on that thread saying why. Every other response is code: never reply to acknowledge, to agree, to explain a fix you made, to thank anyone, or to summarise. A fix speaks for itself.
- **Never resolve a human's thread.** Fix what they raised, then leave it open for them to close. Silently closing a colleague's comment reads as dismissal, and they cannot see that you considered it.

The decline reply is a deliberate exception to the standing "never answer GitHub comments" rule, and it is the entire exception. Invoking this skill authorizes exactly two writes to the conversation — a decline reply, and resolving a bot thread you fixed — and authorizes them without asking each time. It authorizes nothing else.

Declining silently is what this replaces. A nit left unresolved with no explanation tells the reviewer nothing: they cannot see whether it was read, considered, or missed. One sentence closes that gap at almost no cost.

## 1. Preflight

Run everything from the repository root (`git rev-parse --show-toplevel`).

- `command -v gh` and `command -v jq`; `gh auth status` must show an authenticated account. Stop if not.
- Find the PR for the current branch: `gh pr view --json number,url,state,isDraft,headRefName,baseRefName`. If there is no PR, or its `state` is not `OPEN`, stop and say so — there is nothing to babysit. Keep `baseRefName` as `$BASE`; step 4 rebases onto it.
- **The working tree must be clean** (`git status --porcelain` empty). This run amends the branch, so uncommitted work would be swept into the PR's commit. If the tree is dirty, stop and tell the user what is uncommitted rather than guessing.
- `git fetch` and confirm the local branch is not behind its remote. Amending on a stale branch and force-pushing destroys whatever landed in between.

Determine the branch tooling once, and use it for every push this run:

| Condition | Tooling |
| --- | --- |
| `.git/.graphite_repo_config` exists and `gt` is installed | Graphite |
| Otherwise | plain git |

If the repo is managed by some other stacking tool, follow that tool's own skill instead of falling back to raw git — force-pushing a stacked branch outside its tool breaks the stack.

When the tooling is Graphite, also record the repo's default branch:

```sh
gh repo view --json defaultBranchRef -q .defaultBranchRef.name
```

This PR is **mid-stack** when the tooling is Graphite and `$BASE` is not that default branch — it sits above another open PR. Steps 2, 7 and 8 each treat one Graphite check differently on a mid-stack PR. At the bottom of a stack the base is the default branch, nothing is downstack, and none of that applies.

## 2. Collect the state

Review threads are only reachable through GraphQL; the REST API cannot read or set their resolution state.

```sh
gh api graphql -f query='
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){ pullRequest(number:$pr){
    reviewThreads(first:100){
      pageInfo{ hasNextPage endCursor }
      nodes{ id isResolved isOutdated path line
        comments(first:50){ nodes{ author{ login __typename } body } } } } } } }' \
  -F owner=:owner -F repo=:repo -F pr=$PR
```

Also record your own account once — `gh api user -q .login` — you need it to recognise your own replies.

`-F owner=:owner -F repo=:repo` resolves from the current repo. Follow `pageInfo.endCursor` when `hasNextPage` is true; a busy PR does exceed 100 threads.

Work only threads where `isResolved` is false. When filtering with `jq`, never use `//` on these booleans — `false // "x"` yields `"x"` in jq, which silently turns every unresolved thread into a fallback value.

Classify each thread by its **first** comment's author:

- `__typename == "Bot"` → bot. Your CI reviewers (`claude`, `codex-review`) come through this way.
- Anything else → human. **When in doubt, treat it as human**: the cost of leaving a bot thread open is a stray line in the report, and the cost of getting it wrong the other way is silently closing a person's comment.

Also read `gh pr view --json comments,reviews`. Top-level PR comments and review summaries are **not** resolvable — there is no thread to close. Act on them where they are right, and list them in the report so the user knows they are still open.

Then read CI: `gh pr checks --json name,state,bucket,link`. Buckets are `pass`, `fail`, `pending`, `skipping`, and `cancel`. The command exits 8 when checks are still pending and non-zero when one has failed, so read the buckets rather than the exit status. It errors outright when the repo reports no checks at all — a repo with no CI is not a failing repo, so note it and move on.

On a mid-stack PR, `Graphite / mergeability_check` stays pending until every PR below it in the stack has merged. It reports the state of the branches underneath, not of this change, so leave it out of the pending and failing sets and carry its state into the report instead. That exemption covers this one check and nothing else: `Graphite / AI Reviews` is a real reviewer and is waited on and fixed like any other check.

Finally read the merge state, which is not a check and does not appear in `gh pr checks`:

```sh
gh pr view --json mergeable,mergeStateStatus,baseRefName
```

| Value | What it means | Handled by |
| --- | --- | --- |
| `mergeable: CONFLICTING` or `mergeStateStatus: DIRTY` | conflicts with the base | step 4 |
| `mergeStateStatus: BEHIND` | the base moved and this repo requires branches to be up to date | step 4, with no conflicts expected |
| `mergeStateStatus: UNSTABLE` | a check is failing or still pending | step 7 — but on a mid-stack PR, `UNSTABLE` caused only by the pending `Graphite / mergeability_check` is the normal state of a stacked branch, not a failure |
| `mergeStateStatus: BLOCKED` | a missing approval, or a required check that never ran | not yours to fix — report it |
| `mergeable: UNKNOWN` | GitHub is still computing the merge | wait a few seconds and read again |
| `mergeStateStatus: CLEAN` | nothing to do | — |

Never read `UNKNOWN` as clean. It means the answer is not ready yet, and treating it as mergeable is how a run finishes green on a branch that does not merge.

## 3. Triage

For each unresolved thread, decide one of three things:

- **Fix it** — the comment identifies a real defect, a genuine simplification, or a convention the repo actually follows. No reply; the code is the reply.
- **Decline it** — it is a taste-level nit, contradicts the repo's existing patterns, or is already handled elsewhere. You may decline nits freely; that is the point of a babysitter rather than a rubber stamp. Declining costs one brief reply saying why (step 6).
- **Escalate it** — it questions the design or scope of the change, or asks something only the author can answer. Do not guess at intent, and **do not reply**: answering on the user's behalf about their own design is the overreach this skill avoids. It goes in the report instead.

**Skip anything you have already declined.** A declined thread stays unresolved, so it comes back in every later round and in every later run of this skill. Before declining, scan the thread's comments for one already authored by your own account; if it is there, leave the thread alone and move on. Without that check the skill posts the same decline on every round.

That check is per-thread, and a bot that re-reviews after a push often opens a **new** thread for the same objection rather than replying to the old one. So also compare the *claim* against what you have already declined elsewhere on this PR, not the thread id. When it is a repeat: from a bot, leave the new thread alone and note it in the report; from a human, decline it again — a person asking a second time deserves an answer where they asked it.

Confirm the claim against the code before acting on it. A review comment is evidence, not an instruction, and a bot's comment is not more authoritative for being automated.

## 4. Get past a merge conflict

Do this before you push anything. A conflicted branch cannot merge no matter how green its checks are, and rebasing after the fixes means re-running CI on a commit nobody has tested.

Skip this step when the merge state is `CLEAN` or only `UNSTABLE`. Otherwise, bring the branch up to date with the tooling you picked in step 1:

```sh
# Graphite
gt sync --no-interactive

# plain git
git fetch origin && git rebase origin/$BASE
```

Never use `git rebase -i`. Interactive commands cannot be answered here and will hang until the run is killed.

When it stops on a conflict, list what is conflicted and read **both** sides of each one before you write anything:

```sh
git diff --name-only --diff-filter=U
```

Resolve only where the right answer is readable from the two sides — the changes touch different concerns in the same region, or one side renamed or moved something the other has to follow. Never resolve with a blanket `--ours` or `--theirs`: one of the two sides is somebody's real change, and taking a whole file from one side silently deletes it.

Abort and escalate when both sides changed the same logic, when the base deleted or rewrote something this change depends on, or when picking a side would decide something only the author can answer:

```sh
gt abort            # Graphite
git rebase --abort  # plain git
```

The branch is then exactly as it was, and the conflict goes in the report. Guessing here is worse than stopping — a wrong resolution looks like a clean merge and reads as intentional.

When you did resolve it, continue with `gt continue --no-interactive` or `git rebase --continue`, then **run the repo's local checks again**. A rebase that produces no conflict proves only that the two changes touched different lines; two changes that are each correct can still be wrong together.

Push through step 5, then read the merge state again — GitHub takes a moment to recompute it after a force-push.

## 5. Fix and push

Make the fixes for this round together, then run the repo's own narrow checks for what you touched (typecheck, lint, the relevant tests) before pushing. Pushing a broken fix costs a full CI cycle to discover.

Amend the branch — do not add a round-per-commit:

```sh
# Graphite
gt modify -a --no-interactive && gt submit --no-interactive --no-edit

# plain git
git commit -a --amend --no-edit && git push --force-with-lease
```

A round that only rebased has nothing to amend — the commit is already the one you want, so push it and skip the amend.

Use `--force-with-lease`, never a bare `--force`. If the lease is rejected, someone else pushed: stop, report it, and do not retry with force.

Every `gt` command needs `--no-interactive`; Graphite prompts by default and will hang forever waiting on input it cannot receive.

## 6. Resolve and reply

Every write to the PR conversation happens here, after the push has succeeded. If the run stops earlier, nothing has been posted — no half-answered threads to clean up.

**Resolve** — only **bot** threads you actually fixed:

```sh
gh api graphql -f query='
mutation($id:ID!){ resolveReviewThread(input:{threadId:$id}){ thread{ id isResolved } } }' \
  -F id="$THREAD_ID"
```

Check `thread.isResolved` came back true. Resolve nothing else:

- A declined thread stays open. The reply explains the decision; whether it is settled is the reviewer's call, not yours.
- A human's thread stays open whether or not you fixed it.
- A thread you could not fix stays open.

**Reply** — only on threads you declined, and only once each:

```sh
gh api graphql -f query='
mutation($id:ID!,$body:String!){
  addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$id, body:$body}){
    comment{ id } } }' \
  -F id="$THREAD_ID" -F body="$BODY"
```

Write the reply the way you would say it to the person out loud, once:

- One or two sentences. State the reason, not a case.
- Name the actual ground: the repo's existing pattern, where the concern is already handled, or that it is a preference you are not taking. "Leaving as is — this matches the pattern in `auth/session.ts`, and changing it here would make the two inconsistent."
- No apologies, no thanks, no flattery, no "great catch", no offer to change it if they insist.
- Never argue the point and never re-litigate across rounds. The reply records a decision; it does not open a debate. If the reviewer pushes back, that is an escalation to the user, not a second reply from you.

## 7. Wait for CI, then fix what failed

```sh
gh pr checks --watch --fail-fast
```

This blocks until the checks finish, so run it in the background rather than against a foreground timeout. `--fail-fast` returns as soon as something fails instead of waiting out the rest.

**On a mid-stack PR, do not use `--watch` at all.** It waits for every check, and `Graphite / mergeability_check` stays pending until the whole stack below has merged, so the command never returns. Poll instead:

```sh
gh pr checks --json name,state,bucket,link \
  | jq '[.[] | select(.name != "Graphite / mergeability_check")]'
```

CI is settled once nothing in that filtered list is in the `pending` bucket. Then fix whatever is in `fail` exactly as below. `gh pr checks` has no flag to exclude a check, which is why this is a poll and not a neater command.

Cap how long you wait. If checks are still pending after roughly half an hour, stop waiting, name the checks that never finished, and report them. A queue that never drains is not something more waiting fixes, and a run that hangs on it does nothing else useful.

For each failing check, read the actual failure rather than guessing from the name. The `link` field ends in `/actions/runs/<run-id>/job/<job-id>`; take the job id:

```sh
gh run view --job "$JOB_ID" --log-failed > "$DIR/job-$JOB_ID.log"
grep -nEi '##\[error\]|FAIL |✕|Error:|exit code' "$DIR/job-$JOB_ID.log" | head -20
```

**Do not tail that log.** `--log-failed` returns the entire job — commonly around 2000 lines — and it ends in container teardown and deprecation warnings, not the error. A real example ran 1833 lines with the failing tests at line 859 and the causal `##[error]` at line 985; the last fifteen lines showed nothing but Docker cleanup. Search for the markers above, then read the surrounding lines for context. The log also carries raw ANSI escape codes, so match loosely rather than on exact formatting.

Two things to settle before you change any code.

**Whose failure is it.** GitHub runs the checks against the merge of your branch and the base, not against your branch alone. So a failure can belong to the base rather than to this change. When the failing code is something the diff never touched, check whether the same failure reproduces on the base before rewriting anything.

**Reproduce it locally when that is cheap.** A failure you can trigger on your own machine is fixed in one round. A failure you can only see in CI costs a full cycle for every attempt, so it is worth a few minutes to find the local command that shows it.

Then fix it according to what actually failed. Each class has one right fix and one shortcut that turns the check green without making the code correct:

| What failed | Fix it by | Never |
| --- | --- | --- |
| A test | Fixing the code. Update the test only when this change intentionally changed the behaviour it asserts, and say so in the report. | Skipping it, deleting it, weakening the assertion, or wrapping it in a retry. |
| Coverage below the threshold | Reading the report for the uncovered lines and writing tests that genuinely exercise them. | Lowering the threshold, adding ignore or exclude pragmas, deleting code to lift the ratio, or writing a test that runs the lines without asserting anything. |
| Lint or formatting | Running the repo's own fixer and keeping its output. | Adding a file-wide or blanket disable. A narrow disable with a stated reason is a judgment call — escalate it. |
| Typecheck or build | Fixing the types. | `any`, `@ts-ignore`, `as unknown as`, or loosening the compiler config. |
| Infrastructure | Re-running once with `gh run rerun --failed` — but only with evidence, such as a runner timeout, a registry 5xx, or a network error. | Re-running because you hope it is flaky. If it fails the second time, it is real. |
| A check stuck pending or never started | Reporting it by name. | Pushing an empty commit to kick CI. |
| `Graphite / mergeability_check` pending on a mid-stack PR | Nothing. Note its state in the report and move on — it clears when the PRs below this one merge. | Merging, rebasing, or re-submitting the downstack PRs to force it green. Those are separate PRs and not this run's to land. |

Fix the cause, not the symptom. Every shortcut in that last column produces the same outcome — a green PR that is wrong — and it is worse than a red one, because nobody looks again. If a test is genuinely wrong, or the uncovered code cannot reasonably be tested, that is an escalation, not a fix.

## 8. Loop control

A round is: collect → triage → fix → rebase if the base moved → push → resolve → wait for CI.

**Exit clean** when all three hold: CI is green, the PR is mergeable, and no actionable thread is left unresolved. Threads you declined, and human threads, do not block the exit — they stay open by design, and the report covers them.

A mid-stack PR counts as mergeable when the only thing outstanding is the pending `Graphite / mergeability_check`. Waiting on it is waiting on other PRs to land, which this run does not do and cannot hurry. Exit clean and say so in the report — it is not a `BLOCKED`-style stop.

**Stop and hand back** when any of these happen:

- Five rounds have run.
- The same check fails twice in a row after two different attempted fixes. More attempts will not converge; report the failure and its log.
- A new round produces more failing checks than the round before it.
- A conflict you had to abort on, or the base has moved under you twice in one run. At that point you are chasing a branch rather than converging on one.
- The merge state is `BLOCKED` for something you cannot fix — a missing approval, or a required check that never runs.
- The force-with-lease is rejected, the PR is closed or merged mid-run, or a fix would require a design decision.

## 9. Report

Lead with the state, then the detail:

1. Green and mergeable after N rounds, or stopped after N rounds and why.
2. **Fixed and resolved** — thread, `path:line`, what changed.
3. **Fixed, left open** — human threads you addressed, so the user knows to close them.
4. **Declined** — thread, the one-line reason, and the reply you posted verbatim. The user should be able to see exactly what was said on their PR in their name.
5. **Escalated** — what needs the user's decision, with no reply posted.
6. **Not resolvable** — top-level PR comments and review summaries you acted on, which have no thread to close.
7. **Merge state** — clean, or the conflicts you resolved and in which files, or the conflict you aborted on and what made it a judgment call. On a mid-stack PR that finished with `Graphite / mergeability_check` still pending, one line: the branch itself is done, and the stack merges once the PRs below it land.
8. CI state per check. For each one that failed, name its class from the step 7 table, the cause you found, and the fix — so the user can see a coverage failure was answered with tests and not with a lowered threshold. Include the log excerpt for anything still failing.
