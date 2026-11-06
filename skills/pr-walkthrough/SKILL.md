---
name: pr-walkthrough
description: Create a local HTML walkthrough at the final handoff for a pull request you implemented or changed, or when asked to explain an existing PR. Show the architecture first, then trace the code that determines behavior.
---

# Walk through a pull request

Give the reader enough of a mental model to predict what the code will do in a concrete case. Run this once per implementation handoff, after the last code changes and checks in scope. A review, status check, or PR description edit alone does not trigger it. This walkthrough is separate from the PR description.

## Read the implementation

- Resolve the PR from the request or the current branch. Read its purpose, the final diff, and the surrounding callers and tests that explain the change. Verify the base and head you are reading. If the final changes are still local, use the verified comparison base and label the local snapshot.
- Find the entry point, the place where the main decision or state change happens, and what happens downstream. Show the full guard, branch, or state update when the surrounding code helps the reader follow the behavior. Include unchanged code when it explains a boundary or makes the changed behavior possible.
- Skip boilerplate, routine wiring, generated code, and repetitive cases. Keep wiring that changes a contract or explains a consequential decision. One code stop can be enough for a small change.

## Tell the story in this order

1. **Architecture.** Start with one sentence about what changed. Use Mermaid when the reader needs to follow a flow. Use a sequence diagram for calls between components, a flowchart for branching, or a state diagram for lifecycle changes. Label the data or control that crosses each important boundary. Show both paths when a before-and-after comparison explains the decision. Add links beside the diagram to the code stops. Use prose or a short ownership outline when there is no flow. Label any pseudocode as a sketch and keep it here.
2. **Code walkthrough.** Follow a real entry point through one representative input, action, or state. Order the stops by execution or ownership. Show verbatim excerpts and explain the decisions they make and what the next step receives or can assume. Give each excerpt a file path and verified line range. Prefer a source permalink at the exact commit, or the PR diff for deleted lines. For local work, link to the absolute `file:` URL when the file exists. State the revision or label the excerpt as working tree code. Keep the path and line range visible even if a link is unavailable.
3. **Gotchas.** Call out real caveats that change what the reader should expect, such as a fallback, an ordering constraint, or a compatibility edge. Describe when each caveat applies and what happens. Keep consequential caveats visible and omit the section if there are none.
4. **Verification.** Link a relevant test when it demonstrates a key case. State what was actually checked and flag any gap that affects the explanation.

Keep the main path and its excerpts visible. Put worthwhile secondary paths, supporting excerpts, or deeper explanations inside native `<details>` without `open`. Use a `<summary>` that names the case so the reader can decide whether to expand it.

## Show the UI when it helps

Capture the real UI when a visible state or interaction helps explain the change. Put each screenshot next to the architecture step or code that accounts for what the reader sees. Show before and after when the contrast matters. Give each image alt text and a short caption that says what to look at. Follow the `test-assets` skill for where to save raw captures and which files to remove. Embed the selected images as data URLs in the HTML. Verify that the embedded images render, then delete the raw captures before handoff.

## Deliver the HTML

- Use [the HTML starter](assets/walkthrough.html). Adapt the architecture and repeat or remove code stops as needed. If a source link is unavailable, remove the source line under that excerpt and keep the file and lines in the code head. Keep the document self-contained, with no external scripts, styles, fonts, or network requests on load. Escape source excerpts and other text inserted into HTML.
- The starter uses the `html-theme` skill. Follow that skill for any markup you add. When the file is complete, run its `apply_theme.py` on the file without `--web-fonts`, and fix any warning it prints.
- Before writing any generated HTML, run `python3 <skill-dir>/scripts/temporary_output.py` and use the absolute directory it prints. Write drafts, previews, and final HTML only in that directory. This rule also applies to ignored and untracked paths in the repository. If allocation fails, report it. Name the final file for the repository, PR or branch, and revision. Keep the file out of the PR body.
- Render Mermaid locally in the task directory. Use a local Mermaid browser bundle or [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli). For the CLI, run `mmdc -i flow.mmd -o flow.svg -t neutral -b transparent` and `mmdc -i flow.mmd -o flow-dark.svg -t dark -b transparent`. If package downloads are available, `npx --package @mermaid-js/mermaid-cli mmdc` can run the same commands without a global install.
- Embed the SVGs as image data URLs. Set the image width from the SVG viewBox so wider diagrams can scroll without shrinking their labels. Describe the flow in the alt text. If local rendering is unavailable, use linked text steps and disclose the missing chart.
- Open the finished file in a browser if one is available. Check that the diagram renders in light and dark mode, the links jump to the right stops, secondary detail starts collapsed, and the layout fits a narrow window. Check the source references against the revision and remove all template placeholders. Link the file by its absolute path in the final reply. If you cannot produce or verify part of the artifact, say what is missing.

## Clean up

- Delete drafts and preview files before handoff. Keep only the HTML that the reply links to. If a newer walkthrough replaces one from the same task, verify the new file and then remove the old task directory.
- When the user says they have finished with the walkthrough or asks you to remove it, run `python3 <skill-dir>/scripts/temporary_output.py --remove <task-directory>`. Use the same command if you abandon a walkthrough before sharing it. Report any cleanup failure and give the remaining path.
- Each new allocation removes task directories left in the skill's temporary storage for more than seven days. This sweep runs when the skill next allocates a directory.
