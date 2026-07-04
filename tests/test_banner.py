import io

from pyshell import banner


class NonTTYStream(io.StringIO):
    def isatty(self):
        return False


class TTYStream(io.StringIO):
    def isatty(self):
        return True


def test_banner_skips_when_not_a_tty(monkeypatch):
    fake = NonTTYStream()
    monkeypatch.setattr(banner.sys, "stdout", fake)
    banner.show()
    assert fake.getvalue() == ""


def test_banner_skips_when_env_var_set(monkeypatch):
    fake = TTYStream()
    monkeypatch.setattr(banner.sys, "stdout", fake)
    monkeypatch.setenv("PYSHELL_NO_BANNER", "1")
    banner.show()
    assert fake.getvalue() == ""


def test_banner_prints_when_tty(monkeypatch):
    fake = TTYStream()
    monkeypatch.setattr(banner.sys, "stdout", fake)
    monkeypatch.setattr(banner.time, "sleep", lambda _: None)
    monkeypatch.delenv("PYSHELL_NO_BANNER", raising=False)
    banner.show()
    out = fake.getvalue()
    assert "pyshell" in out.lower()
