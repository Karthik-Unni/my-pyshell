"""The Shell class: owns state and runs the read-eval-print loop."""
from __future__ import annotations

import os
import sys

from . import completion
from .executor import run_pipeline
from .history import History
from .jobs import JobTable
from .parser import ParseError, parse_line


class Shell:
    def __init__(self, history_path: str | None = None):
        self.jobs = JobTable()
        self.history = History(path=history_path)
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.last_status = 0
        self._path_cache: dict[str, str | None] = {}

    # -- PATH lookup -----------------------------------------------------
    def find_executable(self, cmd: str) -> str | None:
        if os.sep in cmd:
            return cmd if os.path.isfile(cmd) and os.access(cmd, os.X_OK) else None
        if cmd in self._path_cache:
            return self._path_cache[cmd]
        result = None
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            if not directory:
                continue
            candidate = os.path.join(directory, cmd)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                result = candidate
                break
        self._path_cache[cmd] = result
        return result

    # -- prompt ------------------------------------------------------------
    def prompt(self) -> str:
        cwd = os.getcwd()
        home = os.path.expanduser("~")
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        return f"{os.path.basename(cwd) and cwd}$ "

    # -- main loop -----------------------------------------------------
    def run(self) -> int:
        self.history.load()
        completion.install()
        try:
            while True:
                self.jobs.reap_finished()
                try:
                    sys.stdout.write(self.prompt())
                    sys.stdout.flush()
                    line = input()
                except EOFError:
                    print()
                    break
                except KeyboardInterrupt:
                    print()
                    continue

                if line.strip() == "":
                    continue

                self.history.add(line)
                self.execute(line)
                os.environ["?"] = str(self.last_status)
        finally:
            self.history.append_new()
        return self.last_status

    def execute(self, line: str) -> int:
        try:
            commands, background = parse_line(line)
        except ParseError as e:
            print(f"pyshell: {e}", file=self.stderr)
            self.last_status = 2
            return self.last_status

        if not commands:
            return 0

        try:
            self.last_status = run_pipeline(commands, background, line, self)
        except SystemExit:
            raise
        except OSError as e:
            print(f"pyshell: {e}", file=self.stderr)
            self.last_status = 1
        return self.last_status
