"""Tab completion, hooked into GNU readline.

Completes the first word of a line against builtins + everything on
PATH. Falls back to filename completion for later words (readline
does this itself once we return None enough times).
"""
from __future__ import annotations

import os

from .builtins import BUILTINS


def _path_executables() -> set[str]:
    names = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory or not os.path.isdir(directory):
            continue
        try:
            for entry in os.scandir(directory):
                if entry.is_file() and os.access(entry.path, os.X_OK):
                    names.add(entry.name)
        except PermissionError:
            continue
    return names


class Completer:
    def __init__(self):
        self._matches: list[str] = []

    def complete(self, text: str, state: int) -> str | None:
        import readline

        buf = readline.get_line_buffer()
        is_first_word = buf[:readline.get_begidx()].strip() == ""

        if state == 0:
            if is_first_word:
                candidates = set(BUILTINS) | _path_executables()
            else:
                # filename completion for later words
                dirname, _, prefix = text.rpartition(os.sep)
                search_dir = dirname or "."
                try:
                    candidates = {
                        os.path.join(dirname, e) if dirname else e
                        for e in os.listdir(search_dir)
                        if e.startswith(prefix)
                    }
                except OSError:
                    candidates = set()
            self._matches = sorted(c for c in candidates if c.startswith(text))
        try:
            return self._matches[state]
        except IndexError:
            return None


def install() -> None:
    try:
        import readline
    except ImportError:
        return  # e.g. some minimal/windows builds lack readline
    readline.set_completer(Completer().complete)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \t\n")
