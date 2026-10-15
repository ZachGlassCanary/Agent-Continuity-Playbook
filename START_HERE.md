# START HERE: apply the playbook to a game

You are configuring a **game** repository using this **playbook** repository as the source. The playbook teaches; you perform the setup directly. Do not edit the playbook while doing this, do not run an unknown project's scripts just to inspect it, and never copy this repository's `AGENTS.md`, `SPECIFICATION.md`, `CHANGELOG.md`, `MAINTAINER_NOTES.md`, or `START_HERE.md` into the game.

Normal model: one active coding agent per game at a time; task branches belong to features, not providers.

## 0. Routing and permission

- Playbook only supplied: maintain the playbook (see its `AGENTS.md`). Do not invent a game.
- Playbook plus a game target: continue below. Note the playbook revision (`git -C <playbook> rev-parse HEAD`, and branch).
- Authorized without asking: inspect the game, make reviewed documentation/tooling changes on a setup branch, run safe checks, commit and push that branch, open a (draft) PR.
- Ask first: purchases, new remote repositories or visibility changes, system-wide installs, global Git/client configuration, Unity upgrades, force pushes, destructive cleanup, discarding unexplained work, privileged runners, merging.
- The owner is a designer. Inspect technical facts yourself; ask only for a consequential design choice, permission, or inaccessible information.

## 1. Inspect and preserve

In the game: confirm it is the intended repository; check the remote and default branch, `git status` (staged, unstaged, untracked), worktrees, interrupted operations (merge/rebase/cherry-pick), existing instruction files (`AGENTS.md`, `CLAUDE.md`, nested ones), and open remote branches/PRs. `git fetch` is fine; do not pull, reset, clean, stash, or `git add -A` over existing edits. If authentication fails, remote freshness is unknown. Find a Python 3 interpreter (`python --version`, `py -3 --version`, `python3 --version`) and note the working command; do not install Python system-wide without approval.

## 2. Existing game vs new game

**Existing game.** Find the Unity roots, editor versions (`ProjectSettings/ProjectVersion.txt`), packages, scenes, external assets (LFS, submodules, local packages), test routes, and active work. Record baseline problems. Do not change gameplay, upgrade Unity, or replace existing project knowledge. If another collaboration system exists, map it into the layout below or make a narrowly reviewed transition. Never keep two competing progress systems or two authoritative copies of one design document.

**New game.** Use the installed Unity editor's normal project creation in the explicitly named empty target. Resolve project name, editor version, template/render pipeline, and platform from the request and environment; ask only for materially missing choices; do not substitute a template or download another editor. If Unity is unavailable, prepare the documents only and report project creation and gameplay validation as blocked. Never fabricate a playable game.

An empty repository needs a minimal initial commit before it has a reviewable commit; make that baseline openly, then use a setup branch.

## 3. Copy and adapt

On a setup branch (for example `setup/ai-collaboration`), copy without overwriting existing files; where a file exists, merge by hand, preserving the existing content:

| From playbook | To game |
|---|---|
| `project-template/AGENTS.md` | `AGENTS.md` |
| `project-template/CLAUDE.md` | `CLAUDE.md` (keep other existing instructions; keep the `@AGENTS.md` import) |
| `project-template/docs/ai/*.md` | `docs/ai/` |
| `checks/check_handoff.py` | `tools/ai/check_handoff.py` |
| `checks/tests/test_check_handoff.py` | `tools/ai/tests/test_check_handoff.py` |

Keep `tools/` outside Unity's `Assets` directory. Add `.ai-local/` to `.gitignore` (temporary notes and raw logs). If the project's real file locations differ, map them in `AGENTS.md` and `WORKFLOW.md` and pass explicit `--current`, `--task`, `--context` options to the helper (tested); do not silently diverge.

Then replace every `[FILL IN: ...]` in the copied `docs/ai/` files with facts from the actual project: purpose, Unity versions, how to run, real test commands and what each kind of change requires, external dependencies, the Python command, the playbook source revision, and honest CI/protection limitations. Remove nothing that already applies. Nothing the template says may be recorded as true unless you checked it. With no game task supplied, TASK.md states that the task is setup / awaiting the owner's next task.

Preserve and version `Assets`, `Packages`, `ProjectSettings`, and `.meta` files; keep Unity's package lock; do not track `Library/`, `Temp/`, or other caches (adapt the maintained Unity `.gitignore` rules to the real roots); do not bulk-reserialize scenes or change GUIDs. Never commit secrets, licenses, restricted assets, or private chats.

## 4. Test the helper and check the project

In the game: `python -B -m unittest discover -s tools/ai/tests` (use the real interpreter command). Report the actual counts and outcome. Run whatever real Unity checks exist and are applicable; where no suite exists, say so, and do not call an empty suite passing. If Unity cannot run, record the check as blocked.

## 5. First checkpoint and publication

Follow the checkpoint procedure in the game's `docs/ai/WORKFLOW.md`:

1. Commit the setup work as **C** (explicit staging, no unrelated files).
2. Write `docs/ai/CURRENT.md` with `Reviewed-Commit:` set to C's full ID and honest verification results.
3. Commit **H** changing only CURRENT.
4. `python -B tools/ai/check_handoff.py --ref HEAD --publish --remote <alias> --branch <name>` (use the remote alias you inspected, not an assumed `origin`).
5. Push the branch without force, open a draft PR where possible, and confirm the exact remote commit.

## 6. Optional GitHub check

Where Actions and permissions allow, add `examples/github-handoff.yml` as `.github/workflows/ai-handoff-check.yml`, preserving existing workflows. It checks only the committed record on the real PR head (not the synthetic merge commit) with full history; it does not run Unity or certify tests. Keep actions pinned to full commit IDs and permissions read-only; no self-hosted runner. After it has actually run, basic branch protection (PR required, working check required, no force pushes/deletion) may be configured only if authorized and without weakening stronger existing settings. Report what is configured, observed, unavailable, and advisory-only separately.

## 7. Report to the owner

State: the repository, branch, and published commit as observed on the remote; what was configured; the checks actually run and their results; what could not be checked (Unity, CI, protections, untested clients/OSes); any approval or access needed; and the next game action. If a game task was supplied, begin it now within scope; if not, stop and ask for one. Do not invent features. Merging stays the owner's explicit action.

## Reapplying later

Do not copy files over a configured game. Compare, integrate a targeted patch, preserve instructions, decisions, task state, and code, and record the new playbook revision in `PROJECT.md`.
