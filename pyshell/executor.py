"""Turns parsed Commands into running processes.

Design:
  - Builtins that must mutate the parent shell's own state (cd, exit,
    export, unset) run in-process when they're the sole stage of a
    pipeline and the pipeline isn't backgrounded. Everything else -
    external programs, piped builtins, backgrounded builtins - runs in
    a forked child so pipe plumbing and job control work uniformly.
  - Each pipeline gets its own process group so `jobs`/`fg`/`bg` and
    signals (Ctrl-C, Ctrl-Z equivalents) can target the whole pipeline.
"""
from __future__ import annotations

import os
import sys

from .builtins import BUILTINS
from .parser import Command, Redirections

# Builtins that only make sense running in the shell's own process,
# because they change the shell's state (cwd, env, or terminate it).
STATEFUL_BUILTINS = {"cd", "exit", "export", "unset"}


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

    # Fast path: a single stateful builtin, run inline in the shell process.
    if len(commands) == 1 and not background and commands[0].args[0] in STATEFUL_BUILTINS:
        command = commands[0]
        stdin_fd, stdout_fd, stderr_fd = _open_redirections(command.redirs)
        saved = []
        try:
            if stdout_fd is not None:
                saved.append((1, os.dup(1)))
                os.dup2(stdout_fd, 1)
                os.close(stdout_fd)
            if stderr_fd is not None:
                saved.append((2, os.dup(2)))
                os.dup2(stderr_fd, 2)
                os.close(stderr_fd)
            if stdin_fd is not None:
                os.close(stdin_fd)  # stateful builtins don't read stdin
            fn = BUILTINS[command.args[0]]
            return fn(command.args[1:], shell)
        finally:
            for fd_num, saved_fd in saved:
                os.dup2(saved_fd, fd_num)
                os.close(saved_fd)

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
