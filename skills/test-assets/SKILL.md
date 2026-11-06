---
name: test-assets
description: Where to save temporary test assets and when to delete them. Use whenever you are about to save a screenshot, screen recording, video capture, or similar file to disk to check or show your work. Assets go in a branch folder under ~/Developer/test-assets/, not in the repo, /tmp, or a scratchpad. Delete each task's captures after inspection and presentation unless the human explicitly asks to keep them.
---

# Test assets

Save temporary test assets in `~/Developer/test-assets/<branch>/`. Delete each task's captures after inspection and presentation unless the human explicitly asks to keep them.

Test assets are screenshots, screen recordings, video captures and similar files you make to check or show your work. They are not test fixtures. Fixtures that tests read belong in the repo.

## Save

Name the folder after the current branch. Replace `/` with `-` so the branch is one folder. With a detached HEAD, use the checkout's folder name.

```sh
name=$(git branch --show-current | tr / -)
[ -n "$name" ] || name=$(basename "$(git rev-parse --show-toplevel)")
dir="$HOME/Developer/test-assets/$name"
mkdir -p "$dir"
```

- Point the tool's output path at `$dir`. If a tool saved a file somewhere else, move it into `$dir`.
- Write only inside `$dir`. Do not touch `readme.md` or the folders of other branches.
- Track the files created by the current task. Use distinct names so that earlier captures are not overwritten.
- Never commit test assets.
- When the human asks to keep captures, give their paths in your final reply. Otherwise, report that the temporary captures were removed. Do not link to deleted files.

## Clean up

Inspect each capture and present useful evidence before deleting its local source. Use an inline attachment, a working preview, or a live demo. Check that the presented evidence does not depend on a local file that will be deleted.

If no such presentation method is available, report that presentation is incomplete and delete the temporary capture. Do not retain it only to keep a local link working.

When the task includes creating or updating a PR, screenshots and videos may go in its description. Check that the hosted attachment works before deleting the local source. PR attachments may remain after local cleanup.

Delete only the temporary captures and intermediate files created by the current task. Keep local files only when the human explicitly asks. An open branch or PR does not require local retention.

Leave files from earlier tasks and files the human asked to keep alone. Remove the current branch's folder only when it is empty. Never delete the whole `test-assets` directory.

Report any cleanup failure and the remaining path.
