# Agent-Continuity-Playbook

A playbook that teaches a coding agent how to set up a Unity game (new or existing) so a designer can switch between coding agents, providers, and accounts without losing context. The agent does the setup directly: this repository holds instructions, project templates, and one small read-only handoff check. It is not an installer or a framework.

Normal model: **one active coding agent per game at a time**, task branches named for features (not providers), and frequent published checkpoints.

## Contents

| Path | Purpose |
|---|---|
| `START_HERE.md` | The step-by-step sequence an agent follows to configure a game |
| `project-template/` | Generic `AGENTS.md`, `CLAUDE.md`, and `docs/ai/*` records copied into a game |
| `checks/check_handoff.py` | Read-only helper (Python 3 standard library), copied into games as `tools/ai/` |
| `checks/tests/` | Focused tests for the helper |
| `examples/github-handoff.yml` | Adaptable `ai-handoff-check` GitHub Actions job |
| `SPECIFICATION.md` | The v3 specification this repo implements (maintenance reference) |
| `AGENTS.md`, `CLAUDE.md` | Rules for maintaining *this* repository |

## Prerequisites

Repository access, a terminal, Git, and Python 3 (the helper uses only the standard library). Real Unity work additionally needs the project's Unity editor version and a usable license.

## Prompts

Apply the playbook and start a game task:

```text
Read START_HERE.md in [PLAYBOOK REPOSITORY / REVISION].
Apply that workflow to [GAME REPOSITORY OR LOCAL PATH].
Preserve existing work, use the appropriate Unity environment, and verify setup.
Then begin this task: [MY GAME TASK].
```

Resume with another agent or account:

```text
Open [GAME REPOSITORY OR PATH]. Read AGENTS.md and follow its startup procedure.
Find the actual current remote work, reconcile context and baseline, and resume
our active task. Preserve unfinished work and report missing context honestly.
```

Stop or switch deliberately:

```text
Save the current work and decisions in a truthful recoverable checkpoint.
Commit and push reviewed changes, then verify the intended remote branch.
WIP is fine. Do not merge unfinished work or report unrun checks as passed.
```

Rebuild or extend this repository:

```text
Execute Unity_AI_Collaboration_Playbook_v3.md in this PLAYBOOK repository:
[REPOSITORY URL]
Build the reusable instructions, templates, and focused checks described there.
Do not build an installer or a workflow platform. Verify and publish the setup.
```

## Status

Until the setup branch is merged, the default-branch URL does not contain it; use the branch or revision the owner was given. See `CHANGELOG.md` and `MAINTAINER_NOTES.md` for what has and has not been verified.
