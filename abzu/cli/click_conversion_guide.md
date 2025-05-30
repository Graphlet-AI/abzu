# Click Conversion Guide for Abzu CLI

This document serves as a guide for converting the existing argparse-based CLI to use Click.

## Key Click Features to Leverage

1. **Decorator-based Command Pattern**
   - Use `@click.command()` and `@click.group()` decorators
   - Replace manual subparser creation with nested command groups
   - All commands should be configured to display the default values of arguments via `command(context_settings={"show_default": True})`

2. **Option and Argument Handling**
   - Replace `add_argument()` with `@click.option()` and `@click.argument()`
   - Use Click's built-in type conversion and validation

3. **Command Groups**
   - Use `@click.group()` for organizing commands
   - Add subcommands with the `@group.command()` decorator

4. **Parameter Handling**
   - Leverage built-in type validation and conversion
   - Use `help` parameter for documentation
   - Set defaults with `default` parameter

5. **Context Management**
   - Use Click's context to share state between commands
   - Pass `obj` parameter for shared state

## Conversion Steps

1. **Create Basic Command Structure**

   ```python
   @click.group()
   def cli():
       """Abzu - Industry knowledge extraction."""
       pass
   ```

2. **Add Command Groups**

   ```python
   @cli.group()
   def process():
       """Processing commands."""
       pass
   
   @process.command()
   @click.option("-i", "--input", default=config.get("crawl.semianalysis.input"), help="Input JSONL file path")
   def articles(input):
       """Process articles."""
       # Implementation
   ```

3. **Convert Option Specifications**
   - Replace `add_argument` calls with `@click.option()`
   - Keep the same option names and help text

4. **Implement Entry Points**
   - Replace `main()` function with Click's command handling
   - Update imports for module-specific functions

## Example Conversion

### Before (argparse)

```python
parser = argparse.ArgumentParser(description="Abzu - Industry knowledge extraction")
subparsers = parser.add_subparsers(dest="command", help="Commands")

# Process command
process_cmd = subparsers.add_parser("process", help="Processing commands")
process_subparsers = process_cmd.add_subparsers(dest="subcommand", help="Process subcommands")

# Articles subcommand
articles_cmd = process_subparsers.add_parser("articles", help="Process articles")
articles_cmd.add_argument("-i", "--input", default=config.get("crawl.semianalysis.input"), 
                          help="Input JSONL file path")
```

### After (Click)

```python
@click.group()
def cli():
    """Abzu - Industry knowledge extraction."""
    pass

@cli.group()
def process():
    """Processing commands."""
    pass

@process.command(context_settings={"show_default": True})
@click.option("-i", "--input", default=config.get("crawl.semianalysis.input"), 
              help="Input JSONL file path")
def articles(input):
    """Process articles."""
    from abzu.cli.process_articles import process_main
    return process_main(input_file=input)
```

## Click-Specific Features to Use

1. **Rich Help Text**
   - Automatic help text formatting and display
   - Use docstrings for command descriptions

2. **Auto-completion**
   - Enable shell completion for commands and parameters

3. **Echo Functions**
   - Use `click.echo()` instead of print for consistent output
   - Use `click.secho()` for colored output

4. **Progress Bars**
   - Implement progress reporting with `click.progressbar()`

5. **Prompts and Confirmations**
   - Use `click.prompt()` for user input
   - Use `click.confirm()` for yes/no questions

6. **Default Values**
   - Use `@click.command(context_settings={"show_default": True})` to show default values in help text
