import os

from pyshell.parser import (
    extract_redirections,
    parse_line,
    split_pipeline,
    tokenize,
)


def test_simple_tokenize():
    assert tokenize("echo hello world") == ["echo", "hello", "world"]


def test_double_quotes_preserve_spaces():
    assert tokenize('echo "hello   world"') == ["echo", "hello   world"]


def test_single_quotes_are_fully_literal():
    os.environ["FOO"] = "bar"
    assert tokenize("echo '$FOO'") == ["echo", "$FOO"]


def test_variable_expansion_unquoted():
    os.environ["FOO"] = "bar"
    assert tokenize("echo $FOO") == ["echo", "bar"]


def test_variable_expansion_in_double_quotes():
    os.environ["FOO"] = "bar"
    assert tokenize('echo "$FOO baz"') == ["echo", "bar baz"]


def test_braced_variable():
    os.environ["FOO"] = "bar"
    assert tokenize("echo ${FOO}_x") == ["echo", "bar_x"]


def test_backslash_outside_quotes():
    assert tokenize(r"echo hello\ world") == ["echo", "hello world"]


def test_backslash_inside_double_quotes():
    assert tokenize(r'echo "say \"hi\""') == ["echo", 'say "hi"']


def test_adjacent_quotes_glue_into_one_token():
    assert tokenize('foo"bar baz"qux') == ["foobar bazqux"]


def test_split_pipeline_ignores_pipe_in_quotes():
    assert split_pipeline('echo "a|b" | wc -l') == ['echo "a|b" ', ' wc -l']


def test_split_pipeline_no_pipe():
    assert split_pipeline("echo hi") == ["echo hi"]


def test_extract_redirections_stdout():
    tokens, redirs = extract_redirections(["echo", "hi", ">", "out.txt"])
    assert tokens == ["echo", "hi"]
    assert redirs.stdout_path == "out.txt"
    assert redirs.stdout_append is False


def test_extract_redirections_append_and_stderr():
    tokens, redirs = extract_redirections(
        ["cmd", ">>", "out.log", "2>", "err.log"]
    )
    assert tokens == ["cmd"]
    assert redirs.stdout_path == "out.log"
    assert redirs.stdout_append is True
    assert redirs.stderr_path == "err.log"
    assert redirs.stderr_append is False


def test_parse_line_background_flag():
    commands, background = parse_line("sleep 5 &")
    assert background is True
    assert commands[0].args == ["sleep", "5"]


def test_parse_line_pipeline_of_three():
    commands, background = parse_line("cat file | grep foo | wc -l")
    assert background is False
    assert [c.args for c in commands] == [
        ["cat", "file"],
        ["grep", "foo"],
        ["wc", "-l"],
    ]
