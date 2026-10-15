"""Focused regression tests for check_handoff.py, using temporary Git fixtures.

Run from the repository root:  python -B -m unittest discover -s <this directory>
"""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import check_handoff  # noqa: E402

CURRENT = "docs/ai/CURRENT.md"
OK, FAIL, UNVERIFIABLE = 0, 1, 2

NOTE = """# Current work and handoff
Status: {status}
Task: docs/ai/TASK.md
Reviewed-Commit: {commit}

## Summary
Working on the fixture task.

## Completed
Nothing yet.

## Remaining
Everything.

## Verification
Gameplay check failed on the reviewed commit; tests not run for the rest.

## Problems and uncertainties
Known failing gameplay check.

## Next action
Fix the failing check.

## Other unfinished work
None.
"""


def git_env():
    env = dict(os.environ)
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
    return env


class Repo:
    def __init__(self, path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def git(self, *args, check=True):
        p = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=self.path,
                           env=git_env(), capture_output=True, text=True, encoding="utf-8")
        if check and p.returncode != 0:
            raise AssertionError("git %s failed: %s" % (args, p.stderr))
        return p.stdout.strip()

    def write(self, rel, content):
        f = self.path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8", newline="\n")

    def commit(self, message="c"):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def write_note(self, commit, status="in_progress", path=CURRENT, text=None):
        self.write(path, text if text is not None else NOTE.format(status=status, commit=commit))


def new_repo(base, name="game"):
    """Repo with all context files on branch main; returns (repo, setup commit C0)."""
    repo = Repo(Path(base) / name)
    repo.git("init", "-q", "-b", "main")
    repo.write("AGENTS.md", "rules\n")
    for f in ("PROJECT", "TASK", "DECISIONS", "WORKFLOW"):
        repo.write("docs/ai/%s.md" % f, "%s content\n" % f)
    repo.write("Assets/Player.cs", "class Player {}\n")
    repo.write(CURRENT, "placeholder\n")
    return repo, repo.commit("setup")


def run_check(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = check_handoff.main(list(argv))
    return code, out.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = self._tmp.name
        self.repo, self.c0 = new_repo(self.tmp)

    def check(self, *extra, ref="HEAD"):
        return run_check("--repo", str(self.repo.path), "--ref", ref, *extra)

    def checkpoint(self, status="in_progress"):
        """Source commit C (a code change) followed by a CURRENT-only commit H."""
        self.repo.write("Assets/Player.cs", "class Player { int hp; }\n")
        c = self.repo.commit("source")
        self.repo.write_note(c, status)
        return c, self.repo.commit("handoff")


class RecordTests(Base):
    def test_complete_note_with_current_only_handoff_passes(self):
        c, h = self.checkpoint()
        code, out = self.check()
        self.assertEqual(code, OK, out)
        self.assertIn("Handoff record: CURRENT", out)
        self.assertIn("Recorded work: in_progress", out)
        self.assertIn("Local publication preflight: NOT_CHECKED", out)
        self.assertIn("NOT VERIFIED BY THIS TOOL", out)

    def test_every_legal_status_passes(self):
        for status in check_handoff.STATUSES:
            with self.subTest(status=status):
                self.checkpoint(status)
                self.assertEqual(self.check()[0], OK)

    def test_later_tracked_change_is_stale(self):
        cases = {
            "code": ("Assets/Player.cs", "class Player { int hp2; }\n"),
            "task": ("docs/ai/TASK.md", "new requirement\n"),
            "instructions": ("AGENTS.md", "relaxed rules\n"),
            "new file": ("Assets/New.cs", "class N {}\n"),
        }
        for label, (path, content) in cases.items():
            with self.subTest(label):
                self.checkpoint()
                self.repo.write(path, content)
                self.repo.write_note(self.repo.git("rev-parse", "HEAD~1"))
                self.repo.commit("sneaky")
                code, out = self.check()
                self.assertEqual(code, FAIL, out)
                self.assertIn("Handoff record: STALE", out)
                self.assertIn(path, out)

    def test_deletion_is_stale(self):
        c, h = self.checkpoint()
        (self.repo.path / "Assets/Player.cs").unlink()
        self.repo.commit("delete")
        self.assertIn("Handoff record: STALE", self.check()[1])

    def test_mode_change_is_stale(self):
        self.checkpoint()
        self.repo.git("update-index", "--chmod=+x", "Assets/Player.cs")
        self.repo.git("commit", "-q", "-m", "chmod")
        self.assertIn("Handoff record: STALE", self.check()[1])

    def test_rename_is_stale_and_lists_both_paths(self):
        self.checkpoint()
        self.repo.git("mv", "Assets/Player.cs", "Assets/Hero.cs")
        self.repo.commit("rename")
        code, out = self.check()
        self.assertIn("Handoff record: STALE", out)
        self.assertIn("Assets/Player.cs", out)
        self.assertIn("Assets/Hero.cs", out)

    def test_spaces_and_non_ascii_paths_are_reported(self):
        c, h = self.checkpoint()
        self.repo.write("Assets/My Scène é.unity", "scene\n")
        self.repo.commit("scene")
        code, out = self.check()
        self.assertEqual(code, FAIL)
        self.assertIn("Assets/My Scène é.unity", out)

    def test_custom_current_path_with_space_and_non_ascii_passes(self):
        path = "docs/ai/CURRENT é notes.md"
        self.repo.write("Assets/Player.cs", "class Player { int hp; }\n")
        c = self.repo.commit("source")
        self.repo.write_note(c, path=path)
        self.repo.commit("handoff")
        self.assertEqual(self.check("--current", path)[0], OK)

    def test_wildcard_current_path_is_rejected(self):
        self.checkpoint()
        code, out = self.check("--current", "docs/ai/*.md")
        self.assertNotEqual(code, OK)
        self.assertIn("INVALID", out)

    def test_invalid_notes_do_not_pass(self):
        c, h = self.checkpoint()
        good = NOTE.format(status="in_progress", commit=c)
        bad = {
            "unknown status": good.replace("in_progress", "done"),
            "missing status": good.replace("Status: in_progress\n", ""),
            "duplicate field": good.replace("Task:", "Status: blocked\nTask:"),
            "short commit": good.replace(c, c[:7]),
            "uppercase commit": good.replace(c, c.upper()),
            "missing section": good.replace("## Next action\nFix the failing check.\n\n", ""),
            "empty section": good.replace("Fix the failing check.", "<!-- later -->"),
            "duplicate section": good + "\n## Summary\nagain\n",
            "template placeholder": good.replace("Nothing yet.", "[FILL IN: completed work]"),
            "unsafe task path": good.replace("docs/ai/TASK.md", "../outside.md"),
            "absolute task path": good.replace("docs/ai/TASK.md", "/etc/passwd"),
            "missing task file": good.replace("docs/ai/TASK.md", "docs/ai/NOPE.md"),
            "heading in fence only": good.replace("## Remaining\nEverything.\n",
                                                  "```\n## Remaining\n```\n"),
        }
        for label, note in bad.items():
            with self.subTest(label):
                self.repo.write_note(c, text=note)
                self.repo.commit("bad note")
                code, out = self.check()
                self.assertEqual(code, FAIL, out)
                self.assertIn("Handoff record: INVALID", out)

    def test_unfilled_context_file_is_invalid(self):
        c, h = self.checkpoint()
        self.repo.write("docs/ai/PROJECT.md", "[FILL IN: purpose]\n")
        self.repo.commit("template left in place")
        self.assertIn("Handoff record: INVALID", self.check()[1])

    def test_missing_current_file_is_invalid(self):
        code, out = self.check("--current", "docs/ai/MISSING.md")
        self.assertEqual(code, FAIL)
        self.assertIn("INVALID", out)

    def test_older_ref_uses_its_own_committed_files(self):
        c, h1 = self.checkpoint()
        self.repo.write_note(c, text="garbage\n")
        h2 = self.repo.commit("broken note")
        self.assertEqual(self.check(ref="HEAD")[0], FAIL)
        self.assertEqual(self.check(ref=h1)[0], OK)

    def test_worktree_edits_do_not_change_committed_record_result(self):
        self.checkpoint()
        self.repo.write(CURRENT, "uncommitted garbage\n")
        self.repo.write("Assets/Player.cs", "uncommitted change\n")
        self.assertEqual(self.check()[0], OK)

    def test_unresolvable_ref_is_unverifiable(self):
        code, out = self.check(ref="no-such-ref")
        self.assertEqual(code, UNVERIFIABLE)
        self.assertIn("Handoff record: UNVERIFIABLE", out)

    def test_ref_starting_with_dash_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            self.check(ref="--output=x")
        self.assertEqual(cm.exception.code, 2)

    def test_not_a_repository_is_unverifiable(self):
        empty = Path(self.tmp) / "empty"
        empty.mkdir()
        code, out = run_check("--repo", str(empty))
        self.assertEqual(code, UNVERIFIABLE)

    def test_reviewed_commit_need_not_be_an_ancestor(self):
        self.repo.write("Assets/Player.cs", "class Player { int hp; }\n")
        c = self.repo.commit("source")
        self.repo.git("checkout", "-q", "--orphan", "unrelated")
        self.repo.write_note(c)
        self.repo.commit("handoff on unrelated history")
        self.assertEqual(self.check()[0], OK)

    def test_reviewed_commit_that_is_not_a_commit_is_invalid(self):
        c, h = self.checkpoint()
        tree = self.repo.git("rev-parse", "HEAD^{tree}")
        self.repo.write_note(tree)
        self.repo.commit("points at a tree")
        self.assertIn("Handoff record: INVALID", self.check()[1])


class HistoryTests(Base):
    def test_missing_reviewed_commit_object_is_unverifiable(self):
        self.repo.write_note("0123456789abcdef0123456789abcdef01234567")
        self.repo.commit("note")
        code, out = self.check()
        self.assertEqual(code, UNVERIFIABLE)
        self.assertIn("Handoff record: UNVERIFIABLE", out)

    def clone(self, extra=()):
        dest = Path(self.tmp) / "clone"
        subprocess.run(["git", "clone", "-q", *extra, self.repo.path.as_uri(), str(dest)],
                       check=True, env=git_env(), capture_output=True)
        return dest

    def test_fresh_clone_of_ordinary_merge_keeps_reviewed_commit(self):
        self.repo.git("checkout", "-q", "-b", "task")
        self.checkpoint()
        self.repo.git("checkout", "-q", "main")
        self.repo.git("merge", "-q", "--no-ff", "-m", "merge", "task")
        dest = self.clone(["--single-branch", "--branch", "main"])
        self.assertEqual(run_check("--repo", str(dest))[0], OK)

    def test_squash_merge_loses_reviewed_commit_and_is_not_a_false_pass(self):
        self.repo.git("checkout", "-q", "-b", "task")
        self.checkpoint()
        self.repo.git("checkout", "-q", "main")
        self.repo.git("merge", "-q", "--squash", "task")
        self.repo.commit("squashed")
        self.repo.git("branch", "-q", "-D", "task")
        dest = self.clone(["--single-branch", "--branch", "main"])
        code, out = run_check("--repo", str(dest))
        self.assertEqual(code, UNVERIFIABLE, out)

    def test_shallow_clone_missing_history_is_unverifiable(self):
        self.checkpoint()
        dest = self.clone(["--depth", "1"])
        self.assertEqual(run_check("--repo", str(dest))[0], UNVERIFIABLE)


class PublishTests(Base):
    def setUp(self):
        super().setUp()
        self.remote_path = Path(self.tmp) / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.remote_path)],
                       check=True, env=git_env(), capture_output=True)
        self.repo.git("remote", "add", "upstream", str(self.remote_path))
        self.repo.git("checkout", "-q", "-b", "task/one")
        self.checkpoint()

    def publish(self, *extra, remote="upstream", branch="task/one"):
        return self.check("--publish", "--remote", remote, "--branch", branch, *extra)

    def snapshot(self):
        index = (self.repo.path / ".git" / "index").read_bytes()
        return (self.repo.git("for-each-ref"), self.repo.git("status", "--porcelain", "-uall"),
                self.repo.git("rev-parse", "HEAD"), index)

    def test_pushed_clean_branch_matches(self):
        self.repo.git("push", "-q", "upstream", "task/one")
        code, out = self.publish()
        self.assertEqual(code, OK, out)
        self.assertIn("Local publication preflight: CLEAN", out)
        self.assertIn("Remote Git tip: MATCH", out)

    def test_unpushed_commit_is_mismatch_but_local_is_clean(self):
        self.repo.git("push", "-q", "upstream", "task/one")
        self.repo.write("Assets/Player.cs", "class Player { int more; }\n")
        self.repo.commit("unpushed source")
        self.repo.write_note(self.repo.git("rev-parse", "HEAD"))
        self.repo.commit("unpushed handoff")
        code, out = self.publish()
        self.assertEqual(code, FAIL)
        self.assertIn("Local publication preflight: CLEAN", out)
        self.assertIn("Remote Git tip: MISMATCH", out)

    def test_missing_remote_ref_is_mismatch(self):
        code, out = self.publish()
        self.assertEqual(code, FAIL)
        self.assertIn("Remote Git tip: MISMATCH", out)

    def test_unreachable_remote_is_unverifiable(self):
        self.repo.git("remote", "set-url", "upstream", str(Path(self.tmp) / "does-not-exist.git"))
        code, out = self.publish()
        self.assertEqual(code, UNVERIFIABLE)
        self.assertIn("Remote Git tip: UNVERIFIABLE", out)

    def test_unconfigured_remote_is_unverifiable_and_origin_is_not_assumed(self):
        self.repo.git("push", "-q", "upstream", "task/one")
        code, out = self.publish(remote="origin")
        self.assertEqual(code, UNVERIFIABLE)
        self.assertIn("not configured", out)

    def test_dirty_states_fail_local_preflight_but_report_remote_separately(self):
        self.repo.git("push", "-q", "upstream", "task/one")
        cases = {
            "untracked": lambda: self.repo.write("stray.txt", "x\n"),
            "unstaged": lambda: self.repo.write("Assets/Player.cs", "edited\n"),
            "staged": lambda: (self.repo.write("Assets/Player.cs", "edited\n"),
                               self.repo.git("add", "Assets/Player.cs")),
            "interrupted merge": lambda: (self.repo.path / ".git" / "MERGE_HEAD").write_text(
                self.repo.git("rev-parse", "HEAD") + "\n"),
        }
        for label, make in cases.items():
            with self.subTest(label):
                self.repo.git("reset", "-q", "--hard")
                self.repo.git("clean", "-fdq")
                make()
                code, out = self.publish()
                self.assertEqual(code, FAIL, out)
                self.assertIn("Local publication preflight: DIRTY_OR_INTERRUPTED", out)
                self.assertIn("Remote Git tip: MATCH", out)
                (self.repo.path / ".git" / "MERGE_HEAD").unlink(missing_ok=True)

    def test_detached_head_and_wrong_branch_fail(self):
        self.repo.git("push", "-q", "upstream", "task/one")
        code, out = self.publish(branch="other")
        self.assertIn("DIRTY_OR_INTERRUPTED", out)
        self.repo.git("checkout", "-q", "--detach")
        code, out = self.publish()
        self.assertEqual(code, FAIL)
        self.assertIn("detached", out)

    def test_selected_revision_must_be_head(self):
        self.repo.git("push", "-q", "upstream", "task/one")
        code, out = self.publish("--ref", "HEAD~1")
        self.assertEqual(code, FAIL)
        self.assertIn("is not current HEAD", out)

    def test_publish_requires_remote_and_branch(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            self.check("--publish")
        self.assertEqual(cm.exception.code, 2)

    def test_check_does_not_mutate_repository(self):
        self.repo.git("push", "-q", "upstream", "task/one")
        self.repo.write("stray.txt", "x\n")
        before = self.snapshot()
        self.publish()
        self.check()
        self.assertEqual(before, self.snapshot())


class CommandLineTests(Base):
    def test_script_exit_codes_via_subprocess(self):
        self.checkpoint()
        script = str(Path(check_handoff.__file__))
        ok = subprocess.run([sys.executable, "-B", script, "--repo", str(self.repo.path)],
                            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(ok.returncode, OK, ok.stdout + ok.stderr)
        self.repo.write("Assets/Player.cs", "changed\n")
        self.repo.commit("later change")
        stale = subprocess.run([sys.executable, "-B", script, "--repo", str(self.repo.path)],
                               capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(stale.returncode, FAIL)


class PathProblemTests(unittest.TestCase):
    def test_path_rules(self):
        for bad in ("", "/abs", "../x", "a/../b", "a//b", "a\\b", "-x", "C:/x", "a/.git/b", "a/*.md", "a\0b"):
            self.assertIsNotNone(check_handoff.path_problem(bad), bad)
        for good in ("docs/ai/CURRENT.md", "docs/ai/My Notes é.md"):
            self.assertIsNone(check_handoff.path_problem(good), good)


if __name__ == "__main__":
    unittest.main()
