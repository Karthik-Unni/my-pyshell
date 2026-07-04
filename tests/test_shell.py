import io
import os

import pytest

from pyshell.shell import Shell


@pytest.fixture()
def shell(tmp_path):
    s = Shell(history_path=str(tmp_path / "hist"))
    s.stdout = io.StringIO()
    s.stderr = io.StringIO()
    return s


def test_echo(shell):
    shell.execute("echo hello world")
    assert shell.stdout.getvalue() == "hello world\n"


def test_pwd_matches_cwd(shell):
    shell.execute("pwd")
    assert shell.stdout.getvalue().strip() == os.getcwd()


def test_cd_and_pwd(shell, tmp_path):
    shell.execute(f"cd {tmp_path}")
    shell.execute("pwd")
    assert shell.stdout.getvalue().strip() == str(tmp_path)


def test_cd_missing_dir_reports_error(shell):
    status = shell.execute("cd /no/such/dir/xyz")
    assert status == 1
    assert "No such file or directory" in shell.stderr.getvalue()


def test_type_builtin(shell):
    shell.execute("type echo")
    assert "echo is a shell builtin" in shell.stdout.getvalue()


def test_type_external(shell):
    shell.execute("type ls")
    assert "ls is " in shell.stdout.getvalue()


def test_export_and_expansion(shell):
    shell.execute("export GREETING=hi")
    shell.execute("echo $GREETING there")
    assert shell.stdout.getvalue() == "hi there\n"


def test_unset(shell):
    shell.execute("export TMPVAR=x")
    shell.execute("unset TMPVAR")
    shell.execute("echo $TMPVAR")
    assert shell.stdout.getvalue() == "\n"


def test_redirection_to_file(shell, tmp_path):
    target = tmp_path / "out.txt"
    shell.execute(f"echo hi there > {target}")
    assert target.read_text() == "hi there\n"


def test_append_redirection(shell, tmp_path):
    target = tmp_path / "out.txt"
    shell.execute(f"echo one > {target}")
    shell.execute(f"echo two >> {target}")
    assert target.read_text() == "one\ntwo\n"


def test_command_not_found(shell):
    status = shell.execute("this_command_does_not_exist_xyz")
    assert status == 127
    assert "command not found" in shell.stderr.getvalue()


def test_history_records_commands(shell):
    shell.history.add("echo one")
    shell.history.add("echo two")
    shell.execute("history")
    out = shell.stdout.getvalue()
    assert "echo one" in out
    assert "echo two" in out


def test_background_job_registers(shell):
    shell.execute("sleep 0.2 &")
    assert len(shell.jobs.all_sorted()) == 1
    job = shell.jobs.all_sorted()[0]
    assert "sleep" in job.command
