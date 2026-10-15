# Changelog

## Unreleased

- Correct checkpoint ordering: validate the committed handoff and inspect local state before pushing, then verify the exact remote tip with `--publish` afterward.
- Require the source repository and full playbook commit SHA for each game's independent local copy and deliberate updates.
- Update README status and specification references; carry essential Unity validation and emergency WIP guidance into the project-local workflow.

## 3.0 (2026-10-14)

- Initial implementation of the v3 specification: `START_HERE.md`, `project-template/`, the read-only `checks/check_handoff.py` with focused tests, and an adaptable `ai-handoff-check` workflow example.
- Playbook CI (`.github/workflows/playbook-tests.yml`) runs the helper tests on Linux and Windows.
