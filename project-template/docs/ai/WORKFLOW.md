# Workflow

Local procedures for this project. Adapt paths and commands to what actually exists; record changes in DECISIONS.md.

Handoff check (read-only; Python 3 standard library):

```text
python -B tools/ai/check_handoff.py --ref HEAD
python -B tools/ai/check_handoff.py --ref HEAD --publish --remote <alias> --branch <name>
```

Exit 0: every requested check passed. 1: a check failed (STALE, INVALID, DIRTY_OR_INTERRUPTED, MISMATCH). 2: evidence unavailable or bad invocation (UNVERIFIABLE). A passing check does not prove the game works, that notes are accurate, or that merging is allowed.

Use the first command to validate the committed record before pushing. Inspect local status separately. Use `--publish` after pushing to verify local publication state and the exact remote branch tip; it is read-only and requires the remote to already match local HEAD.

## Startup (every new session, provider, account, or context loss)

1. Read AGENTS.md and this file. Inspect local changes, branch, interrupted operations, and permissions before switching branches or running project commands.
2. Fetch the intended remote. Examine relevant remote task branches and open PRs, not just the default branch. Read candidate TASK/CURRENT as Git objects (`git show <ref>:docs/ai/CURRENT.md`) before checking out. A branch with missing or malformed notes may still hold important work: flag it.
3. Use the task the owner named. Otherwise reconcile CURRENT, paused work, PR state, and diffs. Several plausible tasks is an ambiguity to resolve, not a reason to pick the newest. Confirm any prior writer has stopped.
4. Read the task, PROJECT, relevant DECISIONS, recent changes, and affected code/scenes. Record newer owner requirements before acting.
5. Run the handoff check. If stale, compare the intervening commits and reconstruct real progress. Run the relevant baseline or state the specific limit. Missing context does not authorize unrelated development.
6. Tell the owner briefly: task resumed, key boundary, next action. If the remote is unreachable you cannot claim no newer work exists; do only explicitly safe, limited work.

A note that passes the check is not thereby correct: read and compare it.

## Checkpoint (after meaningful subtasks, before risky changes, before a switch, when context is unreliable)

1. Save editor buffers/scenes. Record changed requirements in TASK, rationale in DECISIONS, project facts in PROJECT.
2. Review all changes, stage intended files explicitly, and commit the task work as **C**. No unrelated edits, caches, secrets, or license files.
3. Run the task's relevant checks against C. Confirm the tested worktree matches C. If Unity import changes files, resolve that and commit a new C.
4. Write CURRENT against C: put C's full ID in `Reviewed-Commit`. WIP, failed, blocked, and not_run results are honest and allowed.
5. Commit **H**, changing only CURRENT.
6. Validate H locally with `python -B tools/ai/check_handoff.py --ref HEAD`. Inspect local status, the intended branch, and interrupted Git operations before pushing; the record-only check does not inspect them.
7. Push the task branch without force.
8. Verify publication with `python -B tools/ai/check_handoff.py --ref HEAD --publish --remote <alias> --branch <name>`, using the inspected remote alias and intended branch. Open/update a draft PR and report the verified remote commit separately from CI results.

Never write H's own ID inside H. Do not commit CI results back into the triggering commit. Before a long test or likely interruption, publish what you have as labeled WIP. Only CURRENT may change between C and H; any other change needs a new reviewed C. Do not advance `Reviewed-Commit` just to silence the check.

For emergency preservation, an incomplete handoff may fail validation: label it honestly and push the reviewed WIP rather than lose it. Verify the remote tip separately, report the failed check, and finish the handoff when possible. Such a branch is not merge-ready.

## Unity validation

- Use the exact editor version and actual test/build procedures recorded in PROJECT. Preserve `.meta` files and GUIDs, package manifests and the package lock, and existing serialization/merge conventions. Keep caches out of commits; do not bulk-reserialize scenes as setup.
- Check that required LFS objects, submodules, local packages, licensed assets, platform modules, and a usable Unity license are available. A matching remote Git tip does not prove these dependencies are accessible to the next agent/account. Do not kill the owner's busy editor.
- For C# or behavior changes, import/compile, run relevant existing automated tests, and perform focused gameplay checks. For scenes, prefabs, assets, settings, or packages, check imports/references and affected scenes/gameplay; run build/platform checks where affected. Prose-only changes do not imply a Unity run.
- Use arguments supported by the installed Test Framework. Inspect fresh result files and logs, test counts, filters, and skipped tests; exit code zero alone is insufficient. Say when no suite exists or intended tests did not run; an empty suite is not a passing suite.
- Record each applicable result as passed, failed, blocked, not_run, or not_applicable, with the actual command/procedure, tested commit, editor/package environment, counts where applicable, and evidence or limitation. Confirm tested inputs match the commit; resolve Unity import changes before claiming they are covered. Required validation that cannot run leaves work WIP or review-blocked.
- For visual behavior or game feel the agent cannot verify, give the designer concrete review steps and expected behavior. Screenshots and code inspection are not completed playtests. Record owner acceptance only when it actually occurred.

## Merging

Only with explicit owner authorization, after reconciling the current base and confirming acceptance criteria, applicable test evidence, and any required gameplay review. Prefer history-preserving merges: squash/rebase can make a reviewed commit unavailable in a fresh clone (the check then reports UNVERIFIABLE; make a fresh handoff on an authorized branch). Keep unfinished work in draft PRs. Never test a rejection by attempting a merge into the stable branch.

## Recovery

| Situation | Action |
|---|---|
| Previous agent disappeared | Preserve accessible edits, inspect history/branches, reconstruct facts and uncertainty, make a truthful WIP handoff. Do not restart from scratch by default. |
| Dirty or partially staged clone | Identify ownership. Never blindly reset, clean, stash, or commit everything. |
| Missing Reviewed-Commit object | Fetch authorized history; otherwise label prior verification unavailable and establish a new reviewed checkpoint. |
| Unpushed work on another machine | Report the access/publication gap; GitHub does not contain it. |
| Conflicting requirements | Preserve sources, apply the real instruction hierarchy, ask the owner about consequential intent. |
| Busy/missing Unity or assets | Preserve WIP, mark blocked checks, work only on independent scope. Do not kill the owner's editor. |
| Broken checker | Preserve work through ordinary Git, label automation broken, repair narrowly. Never erase work to turn the check green. |

## Owner approval

Needed for: Unity upgrades, major architecture or dependency changes, paid services, permission/global config changes, force pushes or history rewriting, destructive cleanup, discarding unexplained work, and merging.

## Project-specific notes
[FILL IN: mapped paths of any pre-existing design docs, LFS/merge-tool arrangements, test routes]
