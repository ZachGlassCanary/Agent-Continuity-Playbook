# Project

Template: replace every `[FILL IN: ...]` with facts from the actual project. Do not put private absolute machine paths here.

## Purpose, goals, non-goals
[FILL IN: link to the authoritative repository design sections for vision and project boundaries; do not maintain a second copy here]

## Approved constraints
[FILL IN: link to approved design constraints; keep technical/environment constraints here, or "none recorded"]

## Design authority

- Current design and open design questions: [DESIGN.md](DESIGN.md).
- Decision rationale, sources and approval: [DECISIONS.md](DECISIONS.md).
- Design history: [DESIGN_CHANGELOG.md](DESIGN_CHANGELOG.md).

Replace these links with existing equivalents when adopting a project. Identify one active repository location for each role; imported duplicates and external copies are not assumed synchronized. Preserve any inaccessible-source gap in CURRENT instead of claiming migration or approval is complete.

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
Source repository: [FILL IN: playbook repository URL]
Revision: [FILL IN: full playbook source commit SHA]. A branch or tag alone is not a source pin. This identifies the committed source copied into this game, not an update registry; the game keeps its own local copy and receives only deliberately reviewed patches.

## CI and protection limitations
[FILL IN: what `ai-handoff-check` and branch protection actually do here, and what is unavailable or advisory only]
