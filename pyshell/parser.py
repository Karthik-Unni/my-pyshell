"""
Tokenizing and parsing for pyshell.

Responsibilities:
  - split_pipeline: split a raw line into pipeline stages on unquoted `|`
  - tokenize:       turn a single stage into word tokens, honoring
                     single quotes, double quotes, and backslash escapes
  - extract_redirections: pull `>`, `>>`, `2>`, `2>>`, `<` out of a token
                     list, returning the remaining command tokens plus
                     a Redirections object describing file targets
"""
from __future__ import annotations

from dataclasses import dataclass


class ParseError(Exception):
    pass


def split_pipeline(line: str) -> list[str]:
    """Split a line into stages on unquoted, unescaped `|`.

    `echo "a|b"` must NOT be split; `echo a | wc` must be split into
    two stages: 'echo a' and ' wc'.
    """
    stages = []
    current = []
    in_single = in_double = False
    i = 0
    while i < len(line):
        c = line[i]
        if in_single:
            current.append(c)
            if c == "'":
                in_single = False
        elif in_double:
            current.append(c)
            if c == '"':
                in_double = False
            elif c == "\\" and i + 1 < len(line):
                current.append(line[i + 1])
                i += 1
        else:
            if c == "'":
                in_single = True
                current.append(c)
            elif c == '"':
                in_double = True
                current.append(c)
            elif c == "\\" and i + 1 < len(line):
                current.append(c)
                current.append(line[i + 1])
                i += 1
            elif c == "|":
                stages.append("".join(current))
                current = []
            else:
                current.append(c)
        i += 1
    stages.append("".join(current))
    if in_single or in_double:
        raise ParseError("unmatched quote")
    return stages


def tokenize(line: str) -> list[str]:
    """Split a single command stage into word tokens.

    Rules (bash-like subset):
      - Outside quotes, backslash escapes the next character literally.
      - Inside single quotes, everything is literal (no escapes).
      - Inside double quotes, backslash only escapes \\, $, ", ` and
        newline; otherwise the backslash is kept literally.
      - Unquoted whitespace separates tokens; runs of whitespace collapse.
      - Adjacent quoted/unquoted chunks glue into a single token, e.g.
        foo"bar baz"qux -> one token: foobar bazqux
    """
    tokens: list[str] = []
    current: list[str] = []
    have_token = False
    in_single = in_double = False
    i = 0
    n = len(line)

    while i < n:
        c = line[i]

        if in_single:
            if c == "'":
                in_single = False
            else:
                current.append(c)

        elif in_double:
            if c == '"':
                in_double = False
            elif c == "\\" and i + 1 < n and line[i + 1] in ('\\', "$", '"', "`", "\n"):
                current.append(line[i + 1])
                i += 1
            else:
                current.append(c)

        else:
            if c.isspace():
                if have_token:
                    tokens.append("".join(current))
                    current = []
                    have_token = False
                i += 1
                continue
            elif c == "'":
                in_single = True
                have_token = True
            elif c == '"':
                in_double = True
                have_token = True
            elif c == "\\" and i + 1 < n:
                current.append(line[i + 1])
                have_token = True
                i += 1
            else:
                current.append(c)
                have_token = True

        i += 1

    if in_single or in_double:
        raise ParseError("unmatched quote")

    if have_token:
        tokens.append("".join(current))

    return tokens


@dataclass
class Redirections:
    stdout_path: str | None = None
    stdout_append: bool = False
    stderr_path: str | None = None
    stderr_append: bool = False
    stdin_path: str | None = None


_REDIR_OPS = {
    ">": ("stdout", False),
    "1>": ("stdout", False),
    ">>": ("stdout", True),
    "1>>": ("stdout", True),
    "2>": ("stderr", False),
    "2>>": ("stderr", True),
    "<": ("stdin", False),
}


def extract_redirections(tokens: list[str]) -> tuple[list[str], Redirections]:
    """Remove redirection operators + targets from a token list."""
    out_tokens: list[str] = []
    redirs = Redirections()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in _REDIR_OPS:
            if i + 1 >= len(tokens):
                raise ParseError(f"syntax error near unexpected token `newline' after `{tok}'")
            target = tokens[i + 1]
            kind, append = _REDIR_OPS[tok]
            if kind == "stdout":
                redirs.stdout_path = target
                redirs.stdout_append = append
            elif kind == "stderr":
                redirs.stderr_path = target
                redirs.stderr_append = append
            else:
                redirs.stdin_path = target
            i += 2
        else:
            out_tokens.append(tok)
            i += 1
    return out_tokens, redirs


@dataclass
class Command:
    args: list[str]
    redirs: Redirections


def parse_line(line: str) -> tuple[list[Command], bool]:
    """Parse a full input line into a pipeline of Commands.

    Returns (commands, background) where background is True if the
    line ended with an unquoted `&`.
    """
    stripped = line.rstrip()
    background = False
    # Detect trailing unquoted `&`
    stage_check = split_pipeline(stripped)
    last = stage_check[-1].rstrip()
    if last.endswith("&") and not last.endswith("\\&"):
        background = True
        stripped = stripped.rstrip()[:-1].rstrip()

    commands = []
    for stage in split_pipeline(stripped):
        stage = stage.strip()
        if stage == "":
            continue
        tokens = tokenize(stage)
        cmd_tokens, redirs = extract_redirections(tokens)
        if not cmd_tokens:
            raise ParseError("syntax error: empty command")
        commands.append(Command(args=cmd_tokens, redirs=redirs))

    return commands, background
