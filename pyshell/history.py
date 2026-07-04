"""Command history: in-memory list plus file persistence."""
from __future__ import annotations

import os


class History:
    def __init__(self, path: str | None = None):
        self.path = path or os.path.expanduser("~/.pyshell_history")
        self.entries: list[str] = []
        self._loaded_count = 0  # entries present at load time, for "append new only"

    def load(self) -> None:
        if os.path.isfile(self.path):
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                self.entries = [line.rstrip("\n") for line in f if line.strip()]
        self._loaded_count = len(self.entries)

    def add(self, line: str) -> None:
        if line.strip() == "":
            return
        self.entries.append(line)

    def write_all(self, path: str | None = None) -> None:
        target = path or self.path
        with open(target, "w", encoding="utf-8") as f:
            for entry in self.entries:
                f.write(entry + "\n")

    def append_new(self, path: str | None = None) -> None:
        """Append only entries added since load() to the history file."""
        target = path or self.path
        new_entries = self.entries[self._loaded_count:]
        if not new_entries:
            return
        with open(target, "a", encoding="utf-8") as f:
            for entry in new_entries:
                f.write(entry + "\n")
        self._loaded_count = len(self.entries)

    def show(self, count: int | None = None) -> list[str]:
        if count is None:
            return list(enumerate(self.entries, start=1))
        return list(enumerate(self.entries, start=1))[-count:]
