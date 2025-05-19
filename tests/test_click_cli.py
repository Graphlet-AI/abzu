import pytest
from click.testing import CliRunner

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
        "api --help",
        [
            "Commands:",
            "  financialdatasets",
            "  sec",
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
            "Usage: cli process articles [OPTIONS] COMMAND [ARGS]...",
            "Commands:",
            "  semianalysis",
            "  theinformation",
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
    (
        "api sec download --help",
        [
            "Usage: cli api sec download [OPTIONS]",
            "--input",
            "--output",
            "--filing-index",
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
