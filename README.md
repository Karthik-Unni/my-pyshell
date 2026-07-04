# pyshell

A Unix-like shell written from scratch in Python — no `shlex`, no
`subprocess`, no `readline` shortcuts for the core logic. It has its
own tokenizer, its own pipeline/redirection handling, and its own job
control built on raw `os.fork`/`os.exec`/`os.pipe`.

## Features

- **REPL** with a `cwd$ ` prompt
- **Builtins**: `cd`, `pwd`, `echo`, `exit`, `type`, `export`, `unset`,
  `env`, `history`, `jobs`, `fg`, `bg`, `help`
- **Quoting**: single quotes (fully literal), double quotes (with
  `\`, `$`, `"` escapes), backslash escaping outside quotes
- **Variable expansion**: `$VAR`, `${VAR}`, `$?` (last exit status)
- **Redirection**: `>`, `>>`, `2>`, `2>>`, `<`
- **Pipelines**: `cmd1 | cmd2 | cmd3`, builtins and externals can be
  mixed in a pipeline
- **Background jobs**: `cmd &`, plus `jobs` / `fg` / `bg`, with real
  process groups so signals target the whole pipeline
- **History**: in-memory during the session, persisted to
  `~/.pyshell_history` on exit (loaded back in on the next start)
- **Tab completion**: builtins + `$PATH` executables for the first
  word, filenames for the rest

## Quick start

```bash
git clone <your-repo-url> pyshell
cd pyshell
python3 -m pyshell
```

Or install it as a command:

```bash
pip install -e .
pyshell
```

## Architecture

```
pyshell/
├── parser.py       # tokenize, split_pipeline, extract_redirections, parse_line
├── builtins.py     # BUILTINS: name -> fn(args, shell) -> exit_status
├── executor.py     # run_pipeline: forking, piping, redirection, backgrounding
├── jobs.py         # JobTable: track/reap/continue background process groups
├── history.py      # History: in-memory list + file persistence
├── completion.py   # readline hook for tab completion
├── shell.py        # Shell class: owns state, runs the REPL loop
└── main.py         # entry point
```

**Design principle:** parsing, execution, and state are separate
modules. A single non-backgrounded builtin runs directly in the
shell's own process (so `cd` actually changes the shell's directory,
and `exit` actually exits). Anything else — external programs, piped
stages, or backgrounded commands — runs in a forked child, wired up
with `os.pipe()`/`os.dup2()` and grouped into a process group with
`os.setpgid()` so `jobs`/`fg`/`bg` can control the whole pipeline.

## Running tests

```bash
pip install pytest
pytest -q
```

## Known limitations / roadmap

These map to natural next commits if you want to keep extending it:

- No globbing (`*.txt` expansion)
- No `&&` / `||` / `;` command chaining
- No here-docs (`<<`)
- No terminal-level job control (`Ctrl-Z` to suspend, `tcsetpgrp` for
  real foreground/background terminal ownership) — `fg`/`bg` work via
  `SIGCONT` and `waitpid` but don't hand over the controlling terminal
- No command substitution (`` `cmd` `` / `$(cmd)`)
- No aliasing or shell functions
- No scripting (`if`/`for`/`while`, reading from a script file)

## License

MIT — do whatever you want with it.
