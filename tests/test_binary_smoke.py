"""Smoke tests for built binaries."""

import subprocess
from pathlib import Path

import pytest

BINARY_PATH = Path("dist/agentrail/agentrail")


@pytest.mark.skipif(not BINARY_PATH.exists(), reason="Binary not built")
def test_binary_version() -> None:
    result = subprocess.run(
        [str(BINARY_PATH), "--version"], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip()


@pytest.mark.skipif(not BINARY_PATH.exists(), reason="Binary not built")
def test_binary_status() -> None:
    result = subprocess.run(
        [str(BINARY_PATH), "status"], capture_output=True, text=True, check=False,
    )
    assert result.returncode in (0, 1)
