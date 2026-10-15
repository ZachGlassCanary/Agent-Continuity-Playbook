# Workflow

Local procedures for this project. Adapt paths and commands to what actually exists; record changes in DECISIONS.md.

Handoff check (read-only; Python 3 standard library):

```text
python -B tools/ai/check_handoff.py --ref HEAD
python -B tools/ai/check_handoff.py --ref HEAD --publish --remote <alias> --branch <name>
```

Exit 0: every requested check passed. 1: a check failed (STALE, INVALID, DIRTY_OR_INTERRUPTED, MISMATCH). 2: evidence unavailable or bad invocation (UNVERIFIABLE). A passing check does not prove the game works, that notes are accurate, or that merging is allowed.

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
6. Run the handoff check with `--publish` on H, push the task branch without force, open/update a draft PR, and confirm the exact remote commit.

Never write H's own ID inside H. Do not commit CI results back into the triggering commit. Before a long test or likely interruption, publish what you have as labeled WIP. Only CURRENT may change between C and H; any other change needs a new reviewed C. Do not advance `Reviewed-Commit` just to silence the check.

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
