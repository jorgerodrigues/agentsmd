---
name: prove-it-works
description: "Apply after completing a task, before declaring it done. Verify the actual result directly with repeatable checks. Show captured screenshots, videos, or live demos when they help a human check the feature, and clean up temporary evidence."
disable-model-invocation: true
---

# Prove It Works

Verify every task output by checking the real thing directly. Do not infer success from proxies, agent reports, or a successful build alone.

Unchecked work has unknown correctness. File times, cached screenshots, and reports from other agents can look like proof. Checking the actual result costs less than acting on a wrong assumption.

## Check the actual result

- Run the changed feature and check the expected behavior. Inspect the actual diff and read the values or state that the task changes.
- Check whether a process is running directly. Do not infer that it is running from files or other derived state.
- Read the actual value from its source. Do not rely on a cached or derived representation.
- When verification fails, check whether the observation method is correct before concluding that the system is wrong.
- Run the narrowest meaningful tests, type checks, and linters for the change. A successful build proves that the build passed. It does not prove that the feature works.
- If a required check cannot run, state what remains unverified and why. Do not declare that part complete.

## Make the check repeatable

Use the smallest deterministic script when it makes the result easier to check again. Run it against the actual artifact and compare the observed result with the expected result. Give the human the command and a concise result.

Keep useful verification code separate from disposable output. Commit a standalone verification script only when large or complex work needs a lasting audit trail, such as a port or migration. Temporary captures and logs follow the cleanup rules below.

## Show the feature when visual evidence helps

Choose evidence that demonstrates the changed behavior. A screenshot can show a visible state or layout. A short screen recording or live demo can show an interaction or a state change. Use direct values and test output for work that has no useful visual result.

- Capture the actual feature from the current running version. Use a browser, simulator, application, or device capture tool that records what happened.
- Do not fabricate evidence with generated images, mockups, edited results, or staged frames that imply an interaction ran. Label seeded data and mocked services. Do not treat them as proof that a real integration works.
- Inspect each screenshot and play back each recording before presenting it. Check that it shows the claimed behavior and contains no unrelated private information.
- Show the capture inline or through a working preview. For a live demo, show the actions and their result. State what was exercised and name the environment, including whether it was a simulator or a physical device.
- State what the capture proves and what remains unchecked. A visible success message alone does not prove that a write reached its destination. Read the actual saved state when that is part of the task.

When the task includes creating or updating a PR, screenshots and videos may go in its description. Use supported attachments or hosted media links that reviewers can open. Check that the attachment is available before deleting the local source. Do not commit captures to the repository or use a local file path as a PR attachment.

## Clean up temporary evidence

Follow [Test Assets](../test-assets/SKILL.md) for capture locations and cleanup. Store screenshots and recordings in `~/Developer/test-assets/<branch>/`. Track the files created by the current task.

After inspection and presentation, delete temporary captures, disposable logs, and intermediate files unless the human explicitly asks to keep them. An open branch or PR is not a reason to keep local captures. A working attachment in the chat or PR may remain after its local source is deleted.

Before deleting a capture, make sure the human can view the presented evidence without the local source. If the viewer needs that source, use a live demo or another presentation method that does not leave a broken link. Do not claim that a tool saved a lasting attachment without checking it.

If no such presentation method is available, report that presentation is incomplete and delete the temporary capture. Do not retain it only to keep a local link working.

Delete only temporary files created by this task. Preserve files from earlier tasks and files the human asked to keep. Remove a capture folder only when it is empty. Report any cleanup failure and the remaining path.

In the final reply, state what was checked and any remaining limits. Link only to working attachments or files the human asked to keep. State that temporary evidence was removed when cleanup is complete.
