# Project

Template: replace every `[FILL IN: ...]` with facts from the actual project. Do not put private absolute machine paths here.

## Purpose, goals, non-goals
[FILL IN: what the game is, what it must do, what it deliberately will not do]

## Approved constraints
[FILL IN: owner-approved constraints, or "none recorded"]

## Systems
Implemented: [FILL IN]
Planned: [FILL IN]
Important files and scenes: [FILL IN]

## Environment
- Unity root(s): [FILL IN]
- Unity editor version(s): [FILL IN: exact version from ProjectSettings/ProjectVersion.txt]
- Target platforms: [FILL IN]
- How to open and run: [FILL IN]
- Python command for the handoff check: [FILL IN: e.g. `python -B` or `py -3 -B`]
- External dependencies and access (LFS, submodules, local packages, licensed assets, platform modules): [FILL IN]

## Validation policy
| Change | Expected validation | Actual command / procedure |
|---|---|---|
| Notes or prose only | Review consistency; run the handoff check | `python -B tools/ai/check_handoff.py --ref HEAD` |
| C# or game behavior | Import/compile, existing automated tests, focused gameplay check | [FILL IN: or "no test suite exists"] |
| Scenes, prefabs, assets, settings, packages | Unity import/reference checks, targeted scene/gameplay checks, build/platform tests where affected | [FILL IN] |
| Workflow, checker, instructions | Helper tests (`python -B -m unittest discover -s tools/ai/tests`) and review of changed safeguards | helper tests |

## Known unknowns
[FILL IN: or "none known"]

## Playbook source
Revision: [FILL IN: playbook commit ID or branch]. This is a source reference, not an update registry.

## CI and protection limitations
[FILL IN: what `ai-handoff-check` and branch protection actually do here, and what is unavailable or advisory only]
