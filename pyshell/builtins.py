"""Builtin shell commands.

Each builtin has the signature: fn(args: list[str], shell: "Shell") -> int
and returns an exit status (0 for success), writing to shell.stdout/stderr
streams so redirection works uniformly for builtins and external commands.
"""
from __future__ import annotations

import os
import sys


def bi_exit(args, shell) -> int:
    code = 0
    if args:
        try:
            code = int(args[0])
        except ValueError:
            code = 0
    raise SystemExit(code)


def bi_echo(args, shell) -> int:
    print(" ".join(args), file=shell.stdout)
    return 0


def bi_pwd(args, shell) -> int:
    print(os.getcwd(), file=shell.stdout)
    return 0


def bi_cd(args, shell) -> int:
    target = args[0] if args else os.environ.get("HOME", os.path.expanduser("~"))
    if target == "-":
        target = os.environ.get("OLDPWD", os.getcwd())
        print(target, file=shell.stdout)
    target = os.path.expanduser(target)
    old = os.getcwd()
    try:
        os.chdir(target)
        os.environ["OLDPWD"] = old
        os.environ["PWD"] = os.getcwd()
        return 0
    except FileNotFoundError:
        print(f"cd: {args[0] if args else target}: No such file or directory", file=shell.stderr)
        return 1
    except NotADirectoryError:
        print(f"cd: {args[0] if args else target}: Not a directory", file=shell.stderr)
        return 1
    except PermissionError:
        print(f"cd: {args[0] if args else target}: Permission denied", file=shell.stderr)
        return 1


def bi_type(args, shell) -> int:
    if not args:
        return 0
    status = 0
    for cmd in args:
        if cmd in BUILTINS:
            print(f"{cmd} is a shell builtin", file=shell.stdout)
        else:
            path = shell.find_executable(cmd)
            if path:
                print(f"{cmd} is {path}", file=shell.stdout)
            else:
                print(f"{cmd}: not found", file=shell.stderr)
                status = 1
    return status


def bi_export(args, shell) -> int:
    if not args:
        for k, v in sorted(os.environ.items()):
            print(f"export {k}={v}", file=shell.stdout)
        return 0
    for arg in args:
        if "=" in arg:
            key, _, value = arg.partition("=")
            os.environ[key] = value
        else:
            os.environ.setdefault(arg, "")
    return 0


def bi_unset(args, shell) -> int:
    for arg in args:
        os.environ.pop(arg, None)
    return 0


def bi_env(args, shell) -> int:
    for k, v in sorted(os.environ.items()):
        print(f"{k}={v}", file=shell.stdout)
    return 0


def bi_help(args, shell) -> int:
    print("pyshell builtins:", file=shell.stdout)
    for name in sorted(BUILTINS):
        print(f"  {name}", file=shell.stdout)
    return 0


def bi_history(args, shell) -> int:
    count = None
    if args:
        try:
            count = int(args[0])
        except ValueError:
            print(f"history: {args[0]}: numeric argument required", file=shell.stderr)
            return 1
    for idx, entry in shell.history.show(count):
        print(f"{idx:>5}  {entry}", file=shell.stdout)
    return 0


def bi_jobs(args, shell) -> int:
    shell.jobs.reap_finished()
    latest = shell.jobs.latest()
    latest_id = latest.job_id if latest else None
    for job in shell.jobs.all_sorted():
        print(shell.jobs.format_line(job, latest_id), file=shell.stdout)
    return 0


def _resolve_job(args, shell):
    if not args:
        return shell.jobs.latest()
    spec = args[0].lstrip("%")
    try:
        job_id = int(spec)
    except ValueError:
        return None
    return shell.jobs.get(job_id)


def bi_fg(args, shell) -> int:
    job = _resolve_job(args, shell)
    if job is None:
        print("fg: no such job", file=shell.stderr)
        return 1
    print(job.command, file=shell.stdout)
    shell.jobs.continue_job(job, foreground=True)
    return 0


def bi_bg(args, shell) -> int:
    job = _resolve_job(args, shell)
    if job is None:
        print("bg: no such job", file=shell.stderr)
        return 1
    shell.jobs.continue_job(job, foreground=False)
    print(f"[{job.job_id}]+ {job.command} &", file=shell.stdout)
    return 0


BUILTINS = {
    "exit": bi_exit,
    "echo": bi_echo,
    "pwd": bi_pwd,
    "cd": bi_cd,
    "type": bi_type,
    "export": bi_export,
    "unset": bi_unset,
    "env": bi_env,
    "help": bi_help,
    "history": bi_history,
    "jobs": bi_jobs,
    "fg": bi_fg,
    "bg": bi_bg,
}
