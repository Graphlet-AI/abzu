import pandas as pd
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
            "  dump",
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
        "crawl --help",
        [
            "Usage: cli crawl [OPTIONS] COMMAND [ARGS]...",
            "  semianalysis",
            "  theinformation",
            "  rss",
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
    (
        "dump returns --help",
        [
            "Usage: cli dump returns [OPTIONS]",
            "--file",
        ],
    ),
    (
        "dump products --help",
        [
            "Usage: cli dump products [OPTIONS]",
            "--file",
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


def test_dump_products_sorted(tmp_path) -> None:
    df = pd.DataFrame(
        [
            {"company_name": "Beta", "name": "ProdB", "description": "B desc"},
            {"company_name": "Alpha", "name": "ProdA", "description": "A desc"},
        ]
    )
    file_path = tmp_path / "products.parquet"
    df.to_parquet(file_path)

    runner = CliRunner()
    result = runner.invoke(cli, ["dump", "products", "-f", str(file_path)])

    assert result.exit_code == 0, result.output
    lines = [line for line in result.output.strip().split("\n") if line]
    assert lines[0].startswith("Company")
    assert "Alpha" in lines[1]
    assert "Beta" in lines[2]
