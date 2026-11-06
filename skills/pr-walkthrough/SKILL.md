---
name: pr-walkthrough
description: Create a local HTML walkthrough at the final handoff for a pull request you implemented or changed, or when asked to explain an existing PR. Show the architecture first, then trace the code that determines behavior.
---

# Walk through a pull request

Give the reader enough of a mental model to predict what the code will do in a concrete case. Run this once per implementation handoff, after the last code changes and checks in scope. A review, status check, or PR description edit alone does not trigger it. This walkthrough is separate from the PR description.

## Read the implementation

- Resolve the PR from the request or the current branch. Read its purpose, the final diff, and the surrounding callers and tests that explain the change. Verify the base and head you are reading. If the final changes are still local, use the verified comparison base and label the local snapshot.
- Find the entry point, the place where the main decision or state change happens, and what happens downstream. Choose the smallest set of code excerpts that explains why the behavior follows from the implementation. Include unchanged code when it explains a boundary or makes the changed behavior possible.
- Leave out wiring, renames, generated files, and repetitive cases unless one of them changes a contract or explains a consequential decision. For a small change, one architecture sketch and one code stop can be enough.

## Tell the story in this order

1. **Architecture.** Start with one sentence about what changed. Show the smallest map that explains it. Use a request sequence for runtime behavior, a state sketch for lifecycle changes, or a shallow tree for ownership or layout. Show the old and new paths together when the contrast explains the decision. Label the data or control that crosses each important boundary. Link relevant parts of the map to the code below.
2. **Code walkthrough.** Follow a real entry point through one representative input, action, or state. Order the stops by execution or ownership. At each stop, show a short verbatim excerpt and explain the decision it makes, why it matters, and what the next step receives or can assume. Cover a failure, retry, or compatibility path when it changes what the reader should expect. Label any pseudocode as a sketch and keep it in the architecture section.
3. **Evidence.** Link each excerpt to a verified file and line range. Prefer source permalinks at the exact commit, or the PR diff for deleted lines. For local work, give the path, line range, and revision or say that the excerpt comes from the working tree. Link a relevant test when it demonstrates a key case. State what was actually checked and flag any gap that affects the explanation.

## Show the UI when it helps

Capture the real UI when a visible state or interaction helps explain the change. Put each screenshot next to the architecture step or code that accounts for what the reader sees. Show before and after when the contrast matters. Give each image alt text and a short caption that says what to look at. Follow the `test-assets` skill for where to save raw captures and which files to remove. Embed the selected images as data URLs in the HTML. Verify that the embedded images render, then delete the raw captures before handoff.

## Deliver the HTML

- Use [the HTML starter](assets/walkthrough.html). Adapt the architecture markup to the change and repeat or remove code stops as needed. Keep the main path visible. Use native disclosure for optional detail. If a source link is unavailable, remove the source line under that excerpt, because the code head already names the file and lines. Keep the document self-contained, with no external scripts, styles, fonts, or network requests on load. Escape source excerpts and other text inserted into HTML.
- The starter uses the `html-theme` skill. Follow that skill for any markup you add. When the file is complete, run its `apply_theme.py` on the file without `--web-fonts`, and fix any warning it prints.
- Before writing any generated HTML, run `python3 <skill-dir>/scripts/temporary_output.py` and use the absolute directory it prints. Write drafts, previews, and final HTML only in that directory. This rule also applies to ignored and untracked paths in the repository. If allocation fails, report it. Name the final file for the repository, PR or branch, and revision. Keep the file out of the PR body.
- Open the finished file in a browser if one is available. Check that the map jumps to the right stops and that the layout fits a narrow window. Check the source references against the revision and remove all template placeholders. Link the file by its absolute path in the final reply. If you cannot produce or verify part of the artifact, say what is missing.

## Clean up

- Delete drafts and preview files before handoff. Keep only the HTML that the reply links to. If a newer walkthrough replaces one from the same task, verify the new file and then remove the old task directory.
- When the user says they have finished with the walkthrough or asks you to remove it, run `python3 <skill-dir>/scripts/temporary_output.py --remove <task-directory>`. Use the same command if you abandon a walkthrough before sharing it. Report any cleanup failure and give the remaining path.
- Each new allocation removes task directories left in the skill's temporary storage for more than seven days. This sweep runs when the skill next allocates a directory.
