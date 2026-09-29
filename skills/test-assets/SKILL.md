---
name: test-assets
description: Where to save temporary test assets and when to delete them. Use whenever you are about to save a screenshot, screen recording, video capture, or similar file to disk to check or show your work — from Playwright, a simulator, screencapture, ffmpeg, or any tool that writes an image or video. Assets go in ~/Developer/test-assets/<branch>, not in the repo, /tmp, or a scratchpad. Delete that folder when the branch is done.
---

# Test assets

Save temporary test assets in `~/Developer/test-assets/<branch>/`. Delete that folder when the branch is done.

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
- Never commit test assets.
- When a task made assets, give the folder path once in your final reply.

## Clean up

Keep the folder while work on the branch goes on. It can hold assets from earlier tasks.

Delete it when the branch is done:

- The PR is merged. `gh pr view --json state -q .state` prints `MERGED`.
- You remove the worktree. Delete the assets first, while you can still read the branch name.
- The user says the branch is done, or asks you to clean up.

```sh
rm -rf "$HOME/Developer/test-assets/${name:?}"
```

`${name:?}` stops the command when `name` is empty. Without it, `rm -rf` would delete the whole `test-assets` folder.

Delete only the current branch's folder. If you are not sure the branch is done, leave the folder and say so.
