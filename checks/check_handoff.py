#!/usr/bin/env python3
"""Read-only handoff check for the AI collaboration playbook.

Checks that the committed handoff record (docs/ai/CURRENT.md) is well formed
and fresh relative to the commit it says it reviewed, and, with --publish,
that local Git state and the exact remote branch agree.

It never stages, commits, fetches, pushes, switches branches, or edits files.
It does not run Unity and does not judge gameplay or whether notes are accurate.

Exit codes: 0 every requested check passed; 1 a check failed (STALE, INVALID,
DIRTY_OR_INTERRUPTED, MISMATCH); 2 required evidence was unavailable or the
invocation was unusable (UNVERIFIABLE, bad arguments, Git failure).
"""
import argparse
import os
import re
import subprocess
import sys

EXIT_OK, EXIT_FAIL, EXIT_UNVERIFIABLE = 0, 1, 2

STATUSES = ("in_progress", "blocked", "ready_for_review", "complete", "idle")
DEFAULT_CURRENT = "docs/ai/CURRENT.md"
DEFAULT_CONTEXT = (
    "AGENTS.md",
    "docs/ai/PROJECT.md",
    "docs/ai/TASK.md",
    "docs/ai/DECISIONS.md",
    "docs/ai/WORKFLOW.md",
)
REQUIRED_SECTIONS = (
    "Summary",
    "Completed",
    "Remaining",
    "Verification",
    "Problems and uncertainties",
    "Next action",
    "Other unfinished work",
)
PLACEHOLDER = "[FILL IN"
FULL_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
HEADER_FIELD = re.compile(r"^([A-Za-z][A-Za-z-]*):[ \t]*(.*?)\s*$")
SECTION_HEADING = re.compile(r"^##[ \t]+(.+?)[ \t#]*$")
INTERRUPTED_MARKERS = (
    "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "REBASE_HEAD",
    "rebase-merge", "rebase-apply", "BISECT_LOG", "sequencer", "index.lock",
)
GIT_TIMEOUT = 30
REMOTE_TIMEOUT = 60
MAX_FILE_BYTES = 256 * 1024
MAX_LISTED = 20


class GitError(Exception):
    """Git could not be run or did not answer: evidence is unavailable."""


class Git:
    def __init__(self, cwd):
        self.cwd = cwd
        env = {k: v for k, v in os.environ.items()
               if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
        env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
        self.env = env

    def run(self, *args, timeout=GIT_TIMEOUT):
        cmd = ["git", "--literal-pathspecs", *args]
        try:
            p = subprocess.run(cmd, cwd=self.cwd, env=self.env, capture_output=True,
                               stdin=subprocess.DEVNULL, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise GitError("git %s timed out after %ss" % (args[0], timeout))
        except OSError as exc:
            raise GitError("cannot run git: %s" % exc)
        return p.returncode, p.stdout, p.stderr


def text(raw):
    return raw.decode("utf-8", errors="replace")


def path_problem(path):
    """Return why `path` is not a safe repository-relative file path, else None."""
    if not path or "\0" in path or any(ord(c) < 32 for c in path):
        return "empty or contains control characters"
    if "\\" in path or path.startswith(("/", "-")) or re.match(r"^[A-Za-z]:", path):
        return "must be a forward-slash repository-relative path"
    if any(c in path for c in "*?["):
        return "wildcards are not allowed"
    for part in path.split("/"):
        if part in ("", ".", "..") or part.lower() == ".git":
            return "contains an empty, '.', '..', or '.git' component"
    return None


def read_blob(git, rev, path):
    """Return (bytes, None) for a regular file in rev's tree, else (None, reason)."""
    problem = path_problem(path)
    if problem:
        return None, "unsafe path %r: %s" % (path, problem)
    rc, out, err = git.run("ls-tree", "-z", rev, "--", path)
    if rc != 0:
        raise GitError("git ls-tree failed: %s" % text(err).strip())
    entry = out.split(b"\0")[0]
    meta, _, name = entry.partition(b"\t")
    fields = meta.split(b" ")
    if not entry or name != path.encode("utf-8") or len(fields) != 3:
        return None, "missing from the committed tree: %s" % path
    if fields[1] != b"blob" or fields[0] == b"120000":
        return None, "not a regular file: %s" % path
    rc, out, err = git.run("cat-file", "-s", "%s:%s" % (rev, path))
    if rc != 0:
        raise GitError("git cat-file failed: %s" % text(err).strip())
    if int(out) > MAX_FILE_BYTES:
        return None, "larger than %d bytes: %s" % (MAX_FILE_BYTES, path)
    rc, out, err = git.run("cat-file", "blob", "%s:%s" % (rev, path))
    if rc != 0:
        raise GitError("git cat-file failed: %s" % text(err).strip())
    return out, None


def decode(raw, path, problems):
    try:
        return raw.decode("utf-8").lstrip("﻿")
    except UnicodeDecodeError:
        problems.append("%s is not valid UTF-8" % path)
        return None


def parse_current(body):
    """Split the note into header fields and ## sections, noting duplicates."""
    header, sections, problems = {}, {}, []
    current, in_fence = None, False
    for line in body.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        heading = None if in_fence else SECTION_HEADING.match(line)
        if heading:
            key = heading.group(1).strip().lower()
            if key in sections:
                problems.append("duplicate section: %s" % heading.group(1).strip())
            sections.setdefault(key, [])
            current = key
        elif current is not None:
            sections[current].append(line)
        elif not in_fence:
            field = HEADER_FIELD.match(line)
            if field:
                if field.group(1) in header:
                    problems.append("duplicate field: %s" % field.group(1))
                header[field.group(1)] = field.group(2)
    return header, sections, problems


def is_blank(section_lines):
    body = re.sub(r"<!--.*?-->", "", "\n".join(section_lines), flags=re.S)
    return not body.strip()


def check_record(git, rev, current_path, task_override, context):
    """Return (state, work_status, details). state: CURRENT|STALE|INVALID|UNVERIFIABLE."""
    problems = []
    raw, why = read_blob(git, rev, current_path)
    if raw is None:
        return "INVALID", "UNKNOWN", [why]
    body = decode(raw, current_path, problems)
    if body is None:
        return "INVALID", "UNKNOWN", problems
    header, sections, dup = parse_current(body)
    problems += dup
    if PLACEHOLDER in body:
        problems.append("%s still contains template placeholders" % current_path)

    status = header.get("Status", "")
    if status not in STATUSES:
        problems.append("Status must be one of: %s (got %r)" % (", ".join(STATUSES), status))
    for name in REQUIRED_SECTIONS:
        lines = sections.get(name.lower())
        if lines is None:
            problems.append("missing section: ## %s" % name)
        elif is_blank(lines):
            problems.append("empty section: ## %s" % name)

    task_path = task_override or header.get("Task", "")
    reviewed = header.get("Reviewed-Commit", "")
    if not task_path:
        problems.append("missing field: Task")
    if not FULL_ID.match(reviewed):
        problems.append("Reviewed-Commit must be a full lowercase commit ID (got %r)" % reviewed)

    required = list(dict.fromkeys(list(context) + ([task_path] if task_path else [])))
    for path in required:
        raw_ctx, why = read_blob(git, rev, path)
        if raw_ctx is None:
            problems.append(why)
            continue
        ctx_text = decode(raw_ctx, path, problems)
        if ctx_text is None:
            continue
        if not ctx_text.strip():
            problems.append("empty file: %s" % path)
        elif PLACEHOLDER in ctx_text:
            problems.append("%s still contains template placeholders" % path)

    shown_status = status if status in STATUSES else "UNKNOWN"
    if problems:
        return "INVALID", shown_status, problems

    rc, out, err = git.run("cat-file", "-t", reviewed)
    if rc != 0:
        return "UNVERIFIABLE", shown_status, [
            "Reviewed-Commit %s is not in this repository; fetch the authorized "
            "history or establish a new reviewed checkpoint" % reviewed]
    if out.strip() != b"commit":
        return "INVALID", shown_status, ["Reviewed-Commit %s is not a commit" % reviewed]

    rc, out, err = git.run("diff", "--no-ext-diff", "--no-textconv", "--no-renames",
                           "--ignore-submodules=none", "--name-only", "-z",
                           reviewed, rev, "--")
    if rc != 0:
        raise GitError("git diff failed: %s" % text(err).strip())
    allowed = current_path.encode("utf-8")
    changed = [p for p in out.split(b"\0") if p and p != allowed]
    if changed:
        details = ["tracked content other than %s changed after Reviewed-Commit:" % current_path]
        details += ["  " + text(p) for p in changed[:MAX_LISTED]]
        if len(changed) > MAX_LISTED:
            details.append("  ... and %d more" % (len(changed) - MAX_LISTED))
        details.append("review the changes and record a new reviewed commit")
        return "STALE", shown_status, details
    return "CURRENT", shown_status, []


def check_local(git, rev, head, branch):
    """Return (state, details) for the local publication preflight."""
    problems = []
    if rev != head:
        problems.append("selected revision %s is not current HEAD %s" % (rev, head))
    rc, out, _ = git.run("symbolic-ref", "--quiet", "HEAD")
    if rc != 0:
        problems.append("HEAD is detached; expected branch %s" % branch)
    elif out.strip() != ("refs/heads/" + branch).encode("utf-8"):
        problems.append("checked-out branch is %s, expected %s" % (text(out).strip(), branch))
    for name in INTERRUPTED_MARKERS:
        rc, out, _ = git.run("rev-parse", "--git-path", name)
        if rc == 0 and os.path.exists(os.path.join(git.cwd, text(out).strip())):
            problems.append("interrupted Git operation or lock present: %s" % name)
    rc, out, err = git.run("status", "--porcelain=v1", "-z", "--untracked-files=all",
                           "--ignore-submodules=none")
    if rc != 0:
        raise GitError("git status failed: %s" % text(err).strip())
    entries = [e for e in out.split(b"\0") if e]
    if entries:
        problems.append("%d uncommitted, staged, or untracked path(s):" % len(entries))
        problems += ["  " + text(e) for e in entries[:MAX_LISTED]]
        if len(entries) > MAX_LISTED:
            problems.append("  ... and %d more" % (len(entries) - MAX_LISTED))
    return ("DIRTY_OR_INTERRUPTED" if problems else "CLEAN"), problems


def check_remote(git, remote, branch, head):
    """Return (state, details) comparing local HEAD with the exact remote branch ref."""
    rc, out, err = git.run("remote")
    if rc != 0 or remote not in text(out).split():
        return "UNVERIFIABLE", ["remote %r is not configured in this repository" % remote]
    ref = "refs/heads/" + branch
    try:
        rc, out, err = git.run("ls-remote", "--exit-code", remote, ref, timeout=REMOTE_TIMEOUT)
    except GitError as exc:
        return "UNVERIFIABLE", [str(exc)]
    if rc == 2 and not out.strip():
        return "MISMATCH", ["%s does not exist on remote %s" % (ref, remote)]
    if rc != 0:
        first = (text(err).strip().splitlines() or ["no error output"])[0]
        return "UNVERIFIABLE", ["could not query remote %s: %s" % (remote, first)]
    tips = {}
    for line in text(out).splitlines():
        sha, _, name = line.partition("\t")
        tips[name] = sha
    if ref not in tips:
        return "MISMATCH", ["%s does not exist on remote %s" % (ref, remote)]
    if tips[ref] != head:
        return "MISMATCH", ["remote %s %s is %s; local HEAD is %s" % (remote, ref, tips[ref], head)]
    return "MATCH", []


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--repo", default=".", help="repository path (default: current directory)")
    p.add_argument("--ref", default="HEAD", help="revision whose committed record is checked")
    p.add_argument("--publish", action="store_true",
                   help="also check local publication state and the exact remote branch tip")
    p.add_argument("--remote", help="configured remote alias (required with --publish)")
    p.add_argument("--branch", help="branch name expected locally and remotely (required with --publish)")
    p.add_argument("--current", default=DEFAULT_CURRENT,
                   help="path of the one file allowed to differ after Reviewed-Commit")
    p.add_argument("--task", help="override the task file named in the record's Task field")
    p.add_argument("--context", action="append",
                   help="required context file; repeat to replace the default list")
    return p


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    if args.publish and not (args.remote and args.branch):
        build_parser().error("--publish requires --remote and --branch")
    if args.publish:
        if args.remote.startswith("-") or args.branch.startswith("-"):
            build_parser().error("remote and branch must not start with '-'")
    if args.ref.startswith("-"):
        build_parser().error("--ref must not start with '-'")

    record, work, details = "UNVERIFIABLE", "UNKNOWN", []
    local, local_details = "NOT_CHECKED", []
    remote, remote_details = "NOT_CHECKED", []
    rev = None
    record_done = False
    try:
        git = Git(args.repo)
        rc, out, err = git.run("rev-parse", "--show-toplevel")
        if rc != 0:
            raise GitError("%s is not a Git repository" % args.repo)
        git = Git(text(out).strip())
        rc, out, err = git.run("rev-parse", "--verify", "--quiet", args.ref + "^{commit}")
        if rc != 0:
            details = ["cannot resolve %r to a commit" % args.ref]
        else:
            rev = text(out).strip()
            context = args.context if args.context else DEFAULT_CONTEXT
            record, work, details = check_record(git, rev, args.current, args.task, context)
        record_done = True
        if args.publish:
            rc, out, err = git.run("rev-parse", "HEAD")
            if rc != 0:
                raise GitError("cannot resolve HEAD")
            head = text(out).strip()
            bad_branch = git.run("check-ref-format", "refs/heads/" + args.branch)[0] != 0
            if bad_branch:
                local, local_details = "DIRTY_OR_INTERRUPTED", ["invalid branch name %r" % args.branch]
                remote, remote_details = "UNVERIFIABLE", ["invalid branch name"]
            else:
                local, local_details = check_local(git, rev or head, head, args.branch)
                remote, remote_details = check_remote(git, args.remote, args.branch, head)
    except GitError as exc:
        if record_done and args.publish:
            if local == "NOT_CHECKED":
                local, local_details = "DIRTY_OR_INTERRUPTED", [str(exc)]
            remote = "UNVERIFIABLE"
            remote_details = remote_details or [str(exc)]
        else:
            record = "UNVERIFIABLE"
            details = details + [str(exc)]

    def show(label, value, extra):
        print("%s: %s" % (label, value))
        for line in extra:
            print("    " + line)

    if rev:
        print("Checked revision: %s" % rev)
    show("Handoff record", record, details)
    print("Recorded work: %s" % work)
    show("Local publication preflight", local, local_details)
    show("Remote Git tip", remote, remote_details)
    print("Gameplay and narrative accuracy: NOT VERIFIED BY THIS TOOL")

    failed = record in ("STALE", "INVALID") or local == "DIRTY_OR_INTERRUPTED" or remote == "MISMATCH"
    unavailable = record == "UNVERIFIABLE" or remote == "UNVERIFIABLE"
    code = EXIT_FAIL if failed else EXIT_UNVERIFIABLE if unavailable else EXIT_OK
    print("Result: %s (exit %d)" % ({0: "PASS", 1: "FAIL", 2: "UNVERIFIABLE"}[code], code))
    return code


if __name__ == "__main__":
    sys.exit(main())
