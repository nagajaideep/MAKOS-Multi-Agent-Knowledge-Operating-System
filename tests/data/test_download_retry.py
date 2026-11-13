import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "data" / "scripts"))

import download_bpi2019 as dl  # noqa: E402


def _http_error(code):
    return urllib.error.HTTPError("http://x", code, "err", {}, None)


def test_retries_on_504_then_succeeds(monkeypatch, tmp_path):
    calls = {"n": 0}

    def flaky(url, dest, size):
        calls["n"] += 1
        if calls["n"] < 3:
            raise _http_error(504)

    monkeypatch.setattr(dl, "_download_once", flaky)
    monkeypatch.setattr(dl.time, "sleep", lambda s: None)
    dl.download("http://x", tmp_path / "f", 10)
    assert calls["n"] == 3


def test_does_not_retry_on_404(monkeypatch, tmp_path):
    def missing(url, dest, size):
        raise _http_error(404)

    monkeypatch.setattr(dl, "_download_once", missing)
    with pytest.raises(urllib.error.HTTPError):
        dl.download("http://x", tmp_path / "f", 10)
