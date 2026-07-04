"""Turns parsed Commands into running processes.

Design:
  - A single, non-backgrounded builtin runs in-process (the shell's
    own process). This is required for state-mutating builtins like
    cd/export/unset/exit, and it's also what makes output correctly
    visible whether the shell's stdout is a real fd or a Python
    object (as in tests). Everything else - external programs, piped
    builtins, backgrounded commands - runs in a forked child so pipe
    plumbing and job control work uniformly.
  - Each pipeline gets its own process group so `jobs`/`fg`/`bg` and
    signals (Ctrl-C, Ctrl-Z equivalents) can target the whole pipeline.
"""
from __future__ import annotations

import os
import sys

from .builtins import BUILTINS
from .parser import Command, Redirections


def _open_redirections(redirs: Redirections):
    """Open any files a Command's redirection targets, returning fds to dup2."""
    stdin_fd = stdout_fd = stderr_fd = None
    if redirs.stdin_path:
        stdin_fd = os.open(redirs.stdin_path, os.O_RDONLY)
    if redirs.stdout_path:
        flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if redirs.stdout_append else os.O_TRUNC)
        stdout_fd = os.open(redirs.stdout_path, flags, 0o644)
    if redirs.stderr_path:
        flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if redirs.stderr_append else os.O_TRUNC)
        stderr_fd = os.open(redirs.stderr_path, flags, 0o644)
    return stdin_fd, stdout_fd, stderr_fd


def _run_builtin_child(command: Command, shell) -> None:
    """Run a builtin inside a forked child, then _exit."""
    fn = BUILTINS[command.args[0]]
    try:
        status = fn(command.args[1:], shell)
    except SystemExit as e:
        status = e.code or 0
    except Exception as e:  # noqa: BLE001 - last line of defense in a child process
        print(f"{command.args[0]}: {e}", file=sys.stderr)
        status = 1
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(status if isinstance(status, int) else 0)


def _exec_external(command: Command, shell) -> None:
    """Replace the current (forked) process image with an external program."""
    path = shell.find_executable(command.args[0])
    if path is None:
        print(f"{command.args[0]}: command not found", file=sys.stderr)
        os._exit(127)
    try:
        os.execv(path, command.args)
    except OSError as e:
        print(f"{command.args[0]}: {e}", file=sys.stderr)
        os._exit(126)


def run_pipeline(commands: list[Command], background: bool, raw_line: str, shell) -> int:
    if not commands:
        return 0

    # Fast path: a single builtin with no pipe and not backgrounded runs
    # inline, in the shell's own process. Redirection is applied by
    # temporarily swapping shell.stdout/stderr to a file handle so it
    # works whether the shell writes to real fds or a Python stream.
    if len(commands) == 1 and not background and commands[0].args[0] in BUILTINS:
        command = commands[0]
        saved_stdout, saved_stderr = shell.stdout, shell.stderr
        opened_files = []
        try:
            if command.redirs.stdin_path:
                # Builtins in this shell don't read stdin from a file;
                # open+close to validate the path and surface errors.
                fd = os.open(command.redirs.stdin_path, os.O_RDONLY)
                os.close(fd)
            if command.redirs.stdout_path:
                mode = "a" if command.redirs.stdout_append else "w"
                f = open(command.redirs.stdout_path, mode)
                opened_files.append(f)
                shell.stdout = f
            if command.redirs.stderr_path:
                mode = "a" if command.redirs.stderr_append else "w"
                f = open(command.redirs.stderr_path, mode)
                opened_files.append(f)
                shell.stderr = f
            fn = BUILTINS[command.args[0]]
            return fn(command.args[1:], shell)
        finally:
            shell.stdout, shell.stderr = saved_stdout, saved_stderr
            for f in opened_files:
                f.close()

    # If it's a single external command, resolve it in the parent first.
    # This lets "command not found" be reported through shell.stderr
    # (correct even when shell.stderr is a non-fd Python stream, e.g.
    # in tests) instead of only ever reaching a real fd 2 in a child.
    if len(commands) == 1 and commands[0].args[0] not in BUILTINS:
        if shell.find_executable(commands[0].args[0]) is None:
            print(f"{commands[0].args[0]}: command not found", file=shell.stderr)
            return 127

    n = len(commands)
    prev_read = None
    pids: list[int] = []
    pgid = None

    for i, command in enumerate(commands):
        is_last = i == n - 1
        pipe_read, pipe_write = (None, None)
        if not is_last:
            pipe_read, pipe_write = os.pipe()

        pid = os.fork()
        if pid == 0:
            # ---- child ----
            if pgid is not None:
                os.setpgid(0, pgid)
            else:
                os.setpgid(0, 0)

            if prev_read is not None:
                os.dup2(prev_read, 0)
                os.close(prev_read)
            if pipe_write is not None:
                os.dup2(pipe_write, 1)
                os.close(pipe_write)
            if pipe_read is not None:
                os.close(pipe_read)

            stdin_fd, stdout_fd, stderr_fd = _open_redirections(command.redirs)
            if stdin_fd is not None:
                os.dup2(stdin_fd, 0)
                os.close(stdin_fd)
            if stdout_fd is not None:
                os.dup2(stdout_fd, 1)
                os.close(stdout_fd)
            if stderr_fd is not None:
                os.dup2(stderr_fd, 2)
                os.close(stderr_fd)

            if command.args[0] in BUILTINS:
                _run_builtin_child(command, shell)
            else:
                _exec_external(command, shell)
            os._exit(1)  # unreachable

        # ---- parent ----
        if pgid is None:
            pgid = pid
        try:
            os.setpgid(pid, pgid)
        except OSError:
            pass  # child may have already done it / already exited
        pids.append(pid)

        if prev_read is not None:
            os.close(prev_read)
        if pipe_write is not None:
            os.close(pipe_write)
        prev_read = pipe_read

    if background:
        job = shell.jobs.add(pgid, pids, raw_line.strip())
        print(f"[{job.job_id}] {pgid}", file=shell.stdout)
        return 0

    status = 0
    for pid in pids:
        _, wstatus = os.waitpid(pid, 0)
        if os.WIFEXITED(wstatus):
            status = os.WEXITSTATUS(wstatus)
        elif os.WIFSIGNALED(wstatus):
            status = 128 + os.WTERMSIG(wstatus)
    return status
