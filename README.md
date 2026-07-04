# my-pyshell 🐚

[![PyPI version](https://badge.fury.io/py/my-pyshell.svg)](https://badge.fury.io/py/my-pyshell)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, custom **Unix-like shell** written entirely in Python. It brings the feel of a classic terminal to your Python environment, complete with a REPL, job control, piping, redirection, and tab completion.

## ✨ Features

- **Interactive REPL** – With an animated ASCII-art banner and colorized prompts.
- **Built-in Commands** – `cd`, `pwd`, `echo`, `export`, `env`, `help`, `type`, `exit`, and more.
- **Tab Completion** – Autocomplete built-ins, file paths, and environment variables.
- **Pipes & Redirection** – Use `|`, `>`, `>>`, and `<` just like in bash.
- **Job Control** – Run commands in the background with `&`, view jobs with `jobs`, and bring them to the foreground with `fg`.
- **Command History** – Persistent history saved across sessions.
- **Cross-Platform** – Works on Linux, macOS, and Windows (with full test coverage on Unix).

## 🚀 Installation

Install directly from PyPI:

```bash
pip install my-pyshell
