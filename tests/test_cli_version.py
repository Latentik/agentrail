from typer.testing import CliRunner

from agentrail.cli import app

runner = CliRunner()



def test_version_option_prints_version() -> None:
    result = runner.invoke(app, ["--version"], catch_exceptions=False)
    assert result.exit_code == 0
    assert result.stdout.strip() == "0.2.1"
