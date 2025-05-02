"""Test script for Click CLI implementation."""

import sys
from pathlib import Path

# Add parent directory to PATH so we can import the click_cli module
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import after sys.path modification
from abzu.cli.click_cli import cli  # noqa: E402

# Test commands and their expected help texts
TEST_COMMANDS = [
    (
        "--help",
        ["Usage: cli [OPTIONS] COMMAND [ARGS]...", "Commands:", "  api", "  crawl", "  process"],
    ),
    (
        "process --help",
        ["Usage: cli process [OPTIONS] COMMAND [ARGS]...", "Commands:", "  articles", "  kg"],
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


def test_click_cli_help_commands():
    """Test that the Click CLI help commands work correctly."""
    from click.testing import CliRunner

    runner = CliRunner()

    print("\n=== Testing Click CLI help commands ===\n")

    for cmd, expected_texts in TEST_COMMANDS:
        print(f"Testing: cli {cmd}")

        # Split the command string into a list for CliRunner
        cmd_args = cmd.split()

        # Run the command with CliRunner
        result = runner.invoke(cli, cmd_args)

        # Check for success and expected text
        if result.exit_code != 0:
            print(f"Error: Command failed with exit code {result.exit_code}")
            print(result.output)
            print(f"Exception: {result.exception}")
            continue

        # Check that all expected texts are in the output
        success = True
        for text in expected_texts:
            if text not in result.output:
                print(f"Error: Expected text '{text}' not found in output")
                success = False

        if success:
            print(f"✓ Command 'cli {cmd}' passed")
        else:
            print(f"✗ Command 'cli {cmd}' failed")
            print(result.output)

        print()  # Add blank line for readability


if __name__ == "__main__":
    # Run the test
    test_click_cli_help_commands()
