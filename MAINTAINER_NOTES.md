# Maintainer notes (never exported to a game)

Only real unfinished playbook work belongs here.

- Not yet exercised against a real Unity project, Unity Test Framework, or a real second agent/account.
- Codex and Claude Code instruction loading (`AGENTS.md`, `CLAUDE.md` import) was not tested in live clients.
- `examples/github-handoff.yml` has not been run in a game repository; only the playbook's own test workflow exists here.
- No branch protection or required checks have been configured on this repository.
- Helper tests (35) passed locally on Windows and in playbook CI on ubuntu-latest and windows-latest (run on commit add34e1). macOS untested.
