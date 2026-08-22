<div align="center">

# 🐚 my-pyshell

**A lightweight, custom Unix-like shell — written entirely in Python.**

Brings the feel of a classic terminal to your Python environment: REPL, job control, piping, redirection, tab completion, and an animated ASCII banner.

[![PyPI version](https://img.shields.io/pypi/v/my-pyshell.svg)](https://pypi.org/project/my-pyshell/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://pypi.org/project/my-pyshell/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Karthik-Unni/my-pyshell/actions/workflows/tests.yml/badge.svg)](https://github.com/Karthik-Unni/my-pyshell/actions)
[![PyPI downloads](https://img.shields.io/pypi/dm/my-pyshell.svg)](https://pypi.org/project/my-pyshell/)

[Install](#-installation) • [Quick Start](#-quick-start) • [Features](#-features) • [Commands](#-built-in-commands) • [Contributing](#-contributing)

</div>

---

```
$ pip install my-pyshell
$ pyshell

  ____        ____  _          _ _
 |  _ \ _   _/ ___|| |__   ___| | |
 | |_) | | | \___ \| '_ \ / _ \ | |
 |  __/| |_| |___) | | | |  __/ | |
 |_|    \__, |____/|_| |_|\___|_|_|
        |___/

pyshell v0.1.1 — type 'help' to get started
➜ ~
```

## ✨ Features

| | |
|---|---|
| 🎬 **Interactive REPL** | Animated ASCII-art banner with tty-aware fallback, colorized prompts |
| 🧰 **Built-in Commands** | `cd`, `pwd`, `echo`, `export`, `env`, `help`, `type`, `exit`, and more |
| ⇥ **Tab Completion** | Autocompletes built-ins, file paths, and environment variables |
| 🔀 **Pipes & Redirection** | `\|`, `>`, `>>`, `<` — just like bash |
| 🧵 **Job Control** | Background jobs with `&`, inspect with `jobs`, resume with `fg` |
| 📜 **Command History** | Persistent across sessions |
| 🖥️ **Cross-Platform** | Linux, macOS, Windows — full test coverage on Unix |

## 🚀 Installation

```bash
pip install my-pyshell
```

Requires **Python 3.10+**.

<details>
<summary><b>Install from source</b></summary>

```bash
git clone https://github.com/Karthik-Unni/my-pyshell.git
cd my-pyshell
pip install -e .
```

</details>

## ⚡ Quick Start

```bash
pyshell
```

```
➜ ~ echo "hello world" | tr a-z A-Z
HELLO WORLD
➜ ~ export NAME=Karthik
➜ ~ echo "hi $NAME" > greeting.txt
➜ ~ cat greeting.txt &
[1] 12345
➜ ~ jobs
[1]+  Running    cat greeting.txt
➜ ~ fg 1
```

## ⌨️ Built-in Commands

<details>
<summary><b>Click to expand full command reference</b></summary>

| Command | Description |
|---|---|
| `cd [dir]` | Change working directory |
| `pwd` | Print working directory |
| `echo [args]` | Print arguments to stdout |
| `export VAR=val` | Set an environment variable |
| `env` | List environment variables |
| `type <cmd>` | Show whether a command is a builtin or external binary |
| `jobs` | List background jobs |
| `fg [job]` | Bring a background job to the foreground |
| `help` | Show available commands |
| `exit` | Exit the shell |

</details>

## 🔀 Piping & Redirection

```bash
cat file.txt | grep "error" | wc -l
sort names.txt > sorted.txt
echo "log entry" >> app.log
python script.py < input.txt
```

## 🧵 Job Control

```bash
long_running_task &     # run in background
jobs                     # list active jobs
fg 1                     # bring job 1 to foreground
```



```

