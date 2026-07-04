"""Startup banner: an animated ASCII-art splash shown when pyshell launches.

Skips itself automatically when stdout isn't a real terminal (piped
input, CI, tests) so it never interferes with scripting or pytest.
Can also be disabled explicitly with PYSHELL_NO_BANNER=1.
"""
from __future__ import annotations

import getpass
import os
import platform
import shutil
import sys
import time

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# A gradient of 256-color codes, cyan -> blue -> magenta, one per art line.
_GRADIENT = [51, 45, 39, 33, 27, 63, 99, 135]

_ART = [
    r"    ____        _____ __         ____",
    r"   / __ \__  __/ ___// /_  ___  / / /",
    r"  / /_/ / / / /\__ \/ __ \/ _ \/ / / ",
    r" / ____/ /_/ /___/ / / / /  __/ / /  ",
    r"/_/    \__, //____/_/ /_/\___/_/_/   ",
    r"      /____/                         ",
]


def _color(code: int) -> str:
    return f"\033[38;5;{code}m"


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _type_out(text: str, delay: float = 0.012) -> None:
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def show(version: str = "0.1.0") -> None:
    """Print the animated banner. No-op when not attached to a real tty."""
    if not sys.stdout.isatty() or os.environ.get("PYSHELL_NO_BANNER"):
        return

    color = _supports_color()
    width = shutil.get_terminal_size(fallback=(80, 24)).columns

    # Draw the ASCII-art logo one line at a time, gradient-colored,
    # each line sliding in with a tiny delay for a "build up" feel.
    for i, line in enumerate(_ART):
        prefix = _color(_GRADIENT[i % len(_GRADIENT)]) if color else ""
        suffix = RESET if color else ""
        sys.stdout.write(prefix + line + suffix + "\n")
        sys.stdout.flush()
        time.sleep(0.05)

    print()

    user = getpass.getuser()
    py_ver = platform.python_version()
    tagline = f"welcome back, BOSS — pyshell v{version} (python {py_ver})"
    if color:
        sys.stdout.write(DIM)
    _type_out(tagline, delay=0.01)
    if color:
        sys.stdout.write(RESET)

    hint = "type 'help' to see builtins, or 'exit' to leave"
    if color:
        sys.stdout.write(DIM)
    print(hint)
    if color:
        sys.stdout.write(RESET)

    print("-" * min(width, 60))
    sys.stdout.flush()
