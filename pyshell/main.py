"""Entry point: `python -m pyshell` or the installed `pyshell` command."""
import sys

from .shell import Shell


def main() -> int:
    shell = Shell()
    try:
        return shell.run()
    except SystemExit as e:
        shell.history.append_new()
        return e.code or 0


if __name__ == "__main__":
    sys.exit(main())
