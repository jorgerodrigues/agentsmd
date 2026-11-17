---
name: implement-issue
description: Take a Linear issue through implementation, independent review, and an HTML walkthrough. Prepare and babysit a pull request by default. Use the no-PR option for work that goes without a pull request.
---

# Implement an issue

Take one Linear issue from its requirements to a reviewed implementation and a walkthrough. Apply the repository's instructions throughout, and honor any limits the user puts on publication or draft status.

Use the PR workflow by default. Use the no-PR workflow when the user passes `--no-pr`, says a PR is unnecessary, or the repository's instructions specify that this change goes without a PR. In that case, implement and review the change, skip stages 3 and 4, and create the walkthrough in stage 5. Commit or push directly only when the request or the repository's direct delivery workflow already authorizes it. Otherwise, leave the reviewed changes local.

## 1. Implement and verify

Use the repository's `fix-issue` skill when it exists. Use a branch that fits the repository's workflow and keep the diff scoped to this issue. If working directly on the default branch, record the starting commit before editing. Ask for the issue only if the request and task context cannot identify it.

In a repository without `fix-issue`, use its sequence. Fetch the issue through Linear MCP and understand the problem. Read any linked Notion page through Notion MCP. Search the code, plan the change, implement it, write and run the relevant tests, and run lint and type checks. If the issue references Sentry, use the repository's authorized Sentry MCP when available. Otherwise, mention the missing Sentry context and carry on.

## 2. Run an independent review

Choose the review skill by the agent running this workflow. Follow the chosen skill through its fix and re-review loop.

- Codex uses `review-with-claude`.
- Claude Code uses `review-with-codex`.
- Other agents default to `review-with-codex`.

Use the PR's actual base or the tracked stack parent for the review when known. For work without a PR, use the verified base for the issue, such as the task branch's fork point or the starting commit when working directly on the default branch. Apply the review skill's host exceptions and stop conditions. Continue only after the review finishes clean on the current changes. If the review cannot finish, report the blocker and preserve the work.

## 3. Submit and mark the PR ready

If the user asked to keep the work local, hand off after review. Otherwise, follow the repository's branch workflow and run any checks it requires before submitting. Prefer `gh` for GitHub operations and native GitHub stacks through `gh stack` from `github/gh-stack` for dependent branches. Use ordinary Git to stage and commit changes. Reuse the PR on the task branch or open a draft with `gh pr create --draft` for an unstacked branch or `gh stack submit --auto` for an authorized stack. Write or update the description with `gh pr edit`, follow the repository's required template and skills, and link the Linear issue.

Graphite configuration or an installed `gt` does not select Graphite. Use it only when the user explicitly requests it, the repository requires it, or `gh` and `gh stack` cannot safely handle the existing stack. State the concrete reason before using it. If native GitHub stacks are unavailable, prefer ordinary PRs through `gh` where the branch chain can be preserved safely. When adopting an existing stack, preserve branch order, PR bases, and existing review work.

An explicit request to run this full workflow includes marking the PR ready. If the user requested a draft, hand off at that stage. If approval is still required, finish the draft and ask before changing its status. Mark only this PR ready with `gh pr ready <pr>` and verify that it is open, ready for review, and at the commit you submitted. Do not use `gh stack submit --open` for this step because it can mark other PRs ready too. Keep the worktree clean for babysitting.

## 4. Babysit the ready PR

Use `babysit-pr` on the same PR. Keep the same tooling preference in linked worktrees. Check both the current Git directory and the common directory for stack configuration when `.git` is a worktree pointer. Verify the installed `gh stack` version's worktree support before changing a stack that spans worktrees. Use `gh stack rebase` and run local checks before `gh stack push`; `gh stack sync` also pushes. Ask before replying to a person and leave human review threads open.

Wait for the skill's green and mergeable outcome. If it stops with a blocker, report the current PR state and what needs to happen before resuming. Refresh the PR description if fixes made it stale. Leave the PR open for the user to merge.

## 5. Create the walkthrough

For a PR, use `pr-walkthrough` once babysitting succeeds. Base it on the final pushed revision, including fixes made during babysitting. Link the PR and report the CI outcome.

For a run without a PR, use `pr-walkthrough` after review and any authorized commit or push. Give it the Linear issue context, the verified comparison base, and the final reviewed revision or working tree as its input. Use those in place of PR data and label the snapshot in the HTML.

In both cases, link the local HTML walkthrough in the final reply and report the checks and review outcome.
