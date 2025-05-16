from click.testing import CliRunner
import pytest

from abzu.cli.click_cli import cli

# Commands to test along with expected text fragments in the output
TEST_COMMANDS = [
    (
        "--help",
        [
            "Usage: cli [OPTIONS] COMMAND [ARGS]...",
            "Commands:",
            "  api",
            "  crawl",
            "  process",
        ],
    ),
    (
        "process --help",
        [
            "Usage: cli process [OPTIONS] COMMAND [ARGS]...",
            "Commands:",
            "  articles",
            "  kg",
        ],
    ),
    (
        "process articles --help",
        [
            "Usage: cli process articles [OPTIONS]",
            "--input",
            "--output",
            "--batch-size",
        ],
    ),
    (
        "api financialdatasets facts --help",
        [
            "Usage: cli api financialdatasets facts [OPTIONS]",
            "--ticker",
            "--cik",
            "--file",
            "--api-key",
            "--pretty",
            "--output",
        ],
    ),
]


@pytest.mark.parametrize("cmd, expected", TEST_COMMANDS)
def test_click_cli_help_commands(cmd: str, expected: list[str]) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, cmd.split())
    assert result.exit_code == 0, result.output
    for text in expected:
        assert text in result.output
