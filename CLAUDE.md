# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development

- Install Dependencies: `poetry install`
- Run CLI: `poetry run abzu`
- Build/Generate abzu/baml_client code: `baml-cli generate`
- Test baml_src code: `baml-cli test`
- Test all: `poetry run pytest tests/`
- Test single: `poetry run pytest tests/path_to_test.py::test_name`
- Test specific cache modes: `poetry run pytest -e ABZU_CACHE_MODE=hybrid tests/test_sync.py`
- Lint: `pre-commit`
- Format: `poetry run black abzu tests`, `poetry run isort abzu tests`
- Type check: `poetry run mypy abzu tests`

### Docker Development (via Taskfile)
- Setup: `task setup` (builds container)
- Start services: `task up` (runs all services in background)
- Stop services: `task down`
- Container shell: `task shell`
- Run tests: `task test`
- Format code: `task format`
- Lint code: `task lint`
- See all tasks: `task help`

### Common Workflows
- Crawl articles: `abzu crawl semianalysis`, `abzu crawl theinformation`, `abzu crawl rss -f feeds.txt`
- Process articles: `abzu process articles semianalysis`
- Build KG: `abzu process kg raw`, then `abzu process kg refine`
- API operations: `abzu api financialdatasets`, `abzu api sec download --ticker NVDA`
- Run pipeline steps: `abzu steps`

## Architecture Overview

### Project Structure
- **abzu/** - Core application code
  - **api/** - External API integrations (SEC, FinancialDatasets)
  - **articles/** - Article processing logic
  - **chat/** - Discord bot functionality
  - **cli/** - Click-based CLI commands (no business logic here)
  - **crawl/** - Web crawlers (Scrapy-based)
  - **dump/** - Data export utilities
  - **kg/** - Knowledge graph processing (Spark/GraphFrames)
  - **reddit/** - Reddit data fetching
  - **spark/** - PySpark data processing utilities
  - **workflows/** - Dapr workflow definitions
- **baml_src/** - BAML templates for LLM extraction
- **data/** - Default data storage directory
- **tests/** - Test suite

### Key Technologies

- **LLM Integration**: BAML (Boundary AI Markup Language) for structured extraction
- **Data Processing**: Apache Spark (PySpark) for ETL and graph operations
- **Graph Database**: Kuzu for graph storage and queries
- **Web Crawling**: Scrapy with custom spiders
- **Caching Modes**: 
  - none: No caching (legacy)
  - local: Redis + disk
  - hybrid: Dapr state store (Redis) + S3/MinIO

### Data Flow
1. **Crawling**: Fetch articles → JSONL files
2. **Processing**: Extract entities via BAML/LLM → processed JSONL
3. **KG Raw**: Build initial graph → Parquet files (vertices/edges)
4. **KG Refine**: Deduplicate and enrich → refined Parquet files
5. **APIs**: Enrich with financial/SEC data

## Code Style

- KISS: KEEP IT SIMPLE STUPID. Do not over-engineer solutions. ESPECIALLY for Spark / PySpark.
- Line length: 100 characters
- Python version: 3.12
- Formatter: black with isort (profile=black)
- Types: Always use type annotations, warn on any return
- Imports: Use absolute imports, organize imports to be PEP compliant with isort (profile=black)
- Error handling: Use specific exception types with logging
- Naming: snake_case for variables/functions, CamelCase for classes
- BAML: Use for LLM-related code, regenerate client with `baml-cli generate`
- Whitespaces: leave no trailing whitespaces, use 4 spaces for indentation, leave no whitespace on blank lines
- Blank lines: Do not indent any blank lines in Python files. Indent should be 0 for these lines. Indent to 0 spaces when replacing a line with a blank line.
- Strings: Use double quotes for strings, use f-strings for string interpolation
- Docstrings: Use Numpy style for docstrings, include type hints in docstrings
- Comments: Use comments to explain complex code, avoid obvious comments
- Tests: Use pytest for testing, include type hints in test functions, use fixtures for setup/teardown
- Tests: Don't make a class to contain unit tests. Just write the tests in pytest style.
- Type hints: Use Python 3.9 type hints for all function parameters and return types. Use `list`, `dict`, `tuple`, etc. instead of `List`, `Dict`, `Tuple` from the `typing` module. Use `Optional` from the `typing` module for optional parameters.
- Type checking: Use mypy for type checking, run mypy before committing code
- Logging: Use logging for error handling, avoid print statements. Always use `from abzu.logs import get_logger` and `logger = get_logger(__name__)`
- Documentation: Use Sphinx for documentation, include docstrings in all public functions/classes
- Code style: Follow PEP 8 for Python code style, use flake8 for linting
- Mypy: Use mypy for type checking, run mypy before committing code. Configure it in `pyproject.toml`, not `mypy.ini`.
- Pre-commit: Use pre-commit for linting and formatting, configure it in `.pre-commit-config.yaml`
- Git: Use git for version control, commit often with clear messages, use branches for new features/bug fixes. Always test new features in the CLI before you commit them.
- Poetry: Use poetry for dependency management and packaging, configure it in `pyproject.toml`
- discord.py package - always use selective imports for `discord` - YES `from discord import x` - NO `import discord`
- Use `abzu.config.Config` - use the `Config` class from `abzu.config` which has an instance abzu.config.config to access configuration values. Do not hardcode configuration values in the codebase. If you need to add a new configuration value, add it to the `config.yml` file and access it through the `Config` class's instance via `from abzu.config import config` and `config.get(key)`.
- External strings - we store all strings in `config.yml` and use the abzu.config.config instance to access them. Do not hardcode strings in the codebase. If you need to add a new string, add it to the config.yml file and access it through the Config class's instance via `from abzu.config import config` and `config.get(key)`.
- Imports - always import up top in PEP8 format. Do not import inside functions or classes. Use absolute imports, not relative imports. Do not use wildcard imports (e.g., `from module import *`). Always import specific classes or functions from modules.
- Submodules - submodules go under `subs/`. Ignore them completely. Never write to submodules in anything you do.
- Space Lines - never create a line with only spaces.
- Imports - don't check if things are installed and handle it with a try/except. Instead, assume they are installed and import them directly. If they are not installed, the code will fail at runtime, which is acceptable in this project.

## Development Guidelines

- Command Line Interfaces - at the end of your coding tasks, please alter the 'abzu' CLI to accommodate the changes. It is a Python / Click CLI.
- Separate logic from the CLI - separate the logic under `abzu` and sub-modules from the command line interface (CLI) code in `abzu.cli`. The CLI should only handle input/output from/to the user and should not contain any business logic. For example the module for `abzu process kg` should be in `abzu.kg.*` and not in `abzu.cli.api`. Similarly, the module for `abzu process articles` should be in `abzu.articles.*` and not in `abzu.cli.api`.
- Help strings - never put the default option values in the help strings. The help strings should only describe what the option does, not what the default value is. The default values are already documented in the `config.yml` file and will be printed via the `@click.command(context_settings={"show_default": True})` decorator of each Click command.
- Read the README - consult the README before taking action. The README contains information about the project and how to use it. If you need to add a new command or change an existing one, consult the README first.
- Update the README - if appropriate, update the README with any new commands or changes to existing commands. The README should always reflect the current state of the project.
- Use Poetry - use poetry for dependency management and packaging. Do not use pip or conda.
- Use BAML - use BAML for LLM-related code. Do not use any other libraries or frameworks for LLM-related code. BAML is an extension of Jinja2 and is used for templating LLM information extraction in this project. Use BAML to generate code for the BAML client and to process data.
- DO NOT WRITE TO the `abzu.baml_client` directory. This directory is generated by the `baml-cli generate` command and should not be modified directly. Instead, use the `baml-cli generate` command to regenerate the client when needed.
- Use PySpark for ETL - use PySpark for ETL and batch data processing to build our knowledge graph. Do not use any other libraries or frameworks for data processing. Use PySpark to take the output of our BAML client and transform it into a knowledge graph.
- PySpark - Do not break up dataflow into functions for loading, computing this, computing that, etc. Create a single function that performs the entire dataflow at hand. Do not check if columns exist, assume they do. Do not check if paths exist, assume they do. We prefer a more linear flow for Spark scripts and simple code over complexity. This only applies to Spark code.
- PySpark - assume the fields are present, don't handle missing fields unless I ask you to.
- PySpark - don't handle obscure edge cases, just implement the logic that I ask DIRECTLY.
- PySpark - SparkSessions should be created BELOW any imports. Do not create SparkSessions at the top of the file.
- Flake8 - fix flake8 errors without being asked and without my verification.
- Black - fix black errors without being asked and without my verification.
- Isort - fix isort errors without being asked and without my verification.
- Mypy - fix mypy errors without being asked and without my verification.
- Pre-commit - fix pre-commit errors without being asked and without my verification.
- New Modules - create a folder for a new module without being asked and without my verification.
- __init__.py - add these files to new module directories without being asked and without my verification.
- Edit Multiple Files at Once - if you need to edit multiple files for a single TODO operation, do so in a single step. Do not create multiple steps for the same task.
- `abzu steps` Command - Add new steps in the data pipeline to the `abzu steps` command. This command is used to run the data pipeline in a specific order. The steps should be added in the order they are executed in the pipeline. If you aren't sure about the order, ask me.
- Git - Keep commit messsages straightforward and to the point - do not put extraneous details, simply summarize the work performed. Do not put anything in commit messages other than a description of the code changes. Do not put "Generated with [Claude Code](https://claude.ai/code)" or anything else relating to Claude or Anthropic.
- Git Log - use the `git log` command to view the commit history to understand the context or recent changes to the codebase. This will help you understand the project better and make informed decisions when writing code.
- Do not use 'rm' to remove files - use `git rm` to remove files from the repository. This will ensure that the files are removed from the git history as well.
- I repeat, NEVER TALK ABOUT YOURSELF IN COMMIT MESSAGES. Do not put "Generated with [Claude Code](https://claude.ai/code)" or anything else relating to Claude or Anthropic in commit messages. Commit messages should only describe the code changes made, not the tool used to make them.
- Do not put 'Co-Authored-By: Claude <noreply@anthropic.com>' in your commit messages.
- Ask questions before mitigating a simple problem with a complex fix.

## Important Notes

### BAML Client Generation
The `abzu/baml_client/` directory is auto-generated. Never edit files in this directory directly. To make changes:
1. Edit the BAML source files in `baml_src/`
2. Run `baml-cli generate` to regenerate the client
3. Test with `baml-cli test`

### Configuration Management

All configuration is centralized in `config.yml`. Access configuration values using:
```python
from abzu.config import config
value = config.get("path.to.key", "default_value")
```

### Logging Best Practices
Always use the centralized logging system:
```python
from abzu.logs import get_logger
logger = get_logger(__name__)

logger.info("Processing started")
logger.error(f"Failed to process: {error}")
```

### Testing Approaches

- Unit tests: Test individual functions/classes in isolation
- Integration tests: Test with real services (Redis, S3, etc.)
- Cache mode tests: Test different caching strategies
- BAML tests: Use `baml-cli test` for LLM extraction testing

### Spark Development

Use the following style guide [README.md](abzu/spark/README.md) for Spark development: @abzu/spark/README.md

For PySpark UDTF (User-Defined Table Functions) usage, refer to the [UDTF Guide](abzu/spark/UDTF.md): @abzu/spark/UDTF.md

In addition, when writing PySpark code:

- Keep dataflows linear and simple
- Don't check for column/path existence
- Write single functions for complete dataflows
- Use DataFrame API over RDDs
- Leverage Spark's lazy evaluation
- For UDTFs, follow the patterns in UDTF.md to avoid column resolution errors

## Alerts

- For long running tasks, use the applescript-mcp server to send me a message when you are done with something. Say "Done with task X" where X is the task you are done with. Alternatively, use the command `osascript -e 'tell application "System Events" to display dialog "Done with task X"'` to send me a message. Send only ONE alert, not multiple alerts.

## Additional Context

### Python Dependencies

- Python 3.12 required
- Core packages: pyspark==3.5.5, scrapy==2.11, baml, kuzu, discord.py
- Development tools: poetry, black, isort, flake8, mypy, pytest
- See pyproject.toml for complete dependency list

### Environment Variables
- `ABZU_CACHE_MODE`: Set caching strategy (none/local/hybrid)
- `SPARK_MODE`: Set Spark execution mode (local/distributed)
- Additional env vars can be configured in Docker setup

### State Management and Caching
- **None mode**: No caching, direct file I/O
- **Local mode**: Redis for state, local disk for artifacts
- **Hybrid mode**: Dapr state store (Redis) + S3/MinIO for artifacts
- State store configuration in `dapr/statestore.yaml`

### Common Pitfalls to Avoid
- Never edit files in `abzu/baml_client/` - always regenerate
- Don't use relative imports - always use absolute imports
- Don't hardcode paths or config values - use config.yml
- Don't break up Spark dataflows into multiple functions
- Don't add default values to Click help strings
- Don't create documentation files unless explicitly requested
