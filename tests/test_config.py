"""Unit tests for the Config class."""

import os
import tempfile
from pathlib import Path

import pytest

from abzu.config import Config


@pytest.fixture
def sample_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(
            """
            # Base data directory configuration
            base_dir: "data"

            # Test section for basic access
            test:
              value: "test_value"
              nested:
                value: "nested_test_value"
              array:
                - "item1"
                - "item2"
                - "item3"
              nested_array:
                paths:
                  - "${base_dir}/path1"
                  - "${base_dir}/path2"
                  - "${base_dir}/path3"

            # Test section for path conversion
            paths:
              simple: "simple_path"
              with_base: "${base_dir}/path"
              nested:
                path: "${base_dir}/nested/path"
              array:
                - "path1"
                - "path2"
                - "path3"
              interpolated_array:
                - "${base_dir}/path1"
                - "${base_dir}/path2"
                - "${base_dir}/path3"

            # Test section for variable interpolation
            interpolation:
              value1: "prefix_${test.value}_suffix"
              value2: "${paths.with_base}/${test.nested.value}"

            # Test section with input/output keys at the same level
            process:
              articles:
                semianalysis:
                  input: "${base_dir}/semianalysis.jsonl"
                  output: "${base_dir}/processed_semianalysis.jsonl"
              kg:
                raw:
                  input:
                    - "${base_dir}/processed_semianalysis.jsonl"
                    - "${base_dir}/processed_theinformation.jsonl"
                  output: "${base_dir}/knowledge_graph"
                  array_inputs:
                    - "${base_dir}/input1.jsonl"
                    - "${base_dir}/input2.jsonl"
            """
        )
        filename = f.name
    yield filename
    os.unlink(filename)


def test_config_init(sample_config_file):
    """Test Config initialization with custom config file."""
    config = Config(sample_config_file)
    assert config.config_file == sample_config_file
    assert isinstance(config._config, dict)
    assert "base_dir" in config._config


def test_get_basic_values(sample_config_file):
    """Test getting basic configuration values."""
    config = Config(sample_config_file)

    # Top level value
    assert config.get("base_dir") == "data"

    # Nested values
    assert config.get("test.value") == "test_value"
    assert config.get("test.nested.value") == "nested_test_value"

    # Default values for non-existent keys
    assert config.get("non_existent_key") is None
    assert config.get("non_existent_key", "default") == "default"
    assert config.get("test.non_existent_key", "default") == "default"


def test_get_array_values(sample_config_file):
    """Test getting array configuration values."""
    config = Config(sample_config_file)

    # Simple array
    array = config.get("test.array")
    assert isinstance(array, list)
    assert len(array) == 3
    assert array == ["item1", "item2", "item3"]

    # Nested array with interpolation
    nested_array = config.get("test.nested_array.paths")
    assert isinstance(nested_array, list)
    assert len(nested_array) == 3
    assert nested_array == ["data/path1", "data/path2", "data/path3"]


def test_get_interpolated_values(sample_config_file):
    """Test getting interpolated configuration values."""
    config = Config(sample_config_file)

    # Simple variable interpolation
    assert config.get("paths.with_base") == "data/path"

    # Nested variable interpolation
    assert config.get("paths.nested.path") == "data/nested/path"

    # Complex variable interpolation
    assert config.get("interpolation.value1") == "prefix_test_value_suffix"
    assert config.get("interpolation.value2") == "data/path/nested_test_value"

    # Array with interpolation
    interpolated_array = config.get("paths.interpolated_array")
    assert isinstance(interpolated_array, list)
    assert interpolated_array == ["data/path1", "data/path2", "data/path3"]


def test_get_input_output_values(sample_config_file):
    """Test getting input and output values at the same level."""
    config = Config(sample_config_file)

    # Get input/output values individually
    semianalysis_input = config.get("process.articles.semianalysis.input")
    semianalysis_output = config.get("process.articles.semianalysis.output")
    assert semianalysis_input == "data/semianalysis.jsonl"
    assert semianalysis_output == "data/processed_semianalysis.jsonl"

    # Get input/output values from a different section
    kg_raw_input = config.get("process.kg.raw.input")
    kg_raw_output = config.get("process.kg.raw.output")
    assert isinstance(kg_raw_input, list)
    assert kg_raw_input == [
        "data/processed_semianalysis.jsonl",
        "data/processed_theinformation.jsonl",
    ]
    assert kg_raw_output == "data/knowledge_graph"

    # Get array inputs
    kg_array_inputs = config.get("process.kg.raw.array_inputs")
    assert isinstance(kg_array_inputs, list)
    assert kg_array_inputs == ["data/input1.jsonl", "data/input2.jsonl"]


def test_get_path(sample_config_file):
    """Test getting configuration values as Path objects."""
    config = Config(sample_config_file)

    # Simple path
    path = config.get_path("paths.simple")
    assert isinstance(path, Path)
    assert str(path) == "simple_path"

    # Path with interpolation
    path = config.get_path("paths.with_base")
    assert isinstance(path, Path)
    assert str(path) == "data/path"

    # Non-existent path with default
    path = config.get_path("non_existent_path", "default_path")
    assert isinstance(path, Path)
    assert str(path) == "default_path"

    # Non-existent path without default should raise an error
    with pytest.raises(ValueError):
        config.get_path("non_existent_path")


def test_get_path_array(sample_config_file):
    """Test getting array of paths."""
    config = Config(sample_config_file)

    # Simple array of paths
    paths = config.get_path("paths.array")
    assert isinstance(paths, list)
    assert len(paths) == 3
    assert all(isinstance(path, Path) for path in paths)
    assert [str(path) for path in paths] == ["path1", "path2", "path3"]

    # Interpolated array of paths
    paths = config.get_path("paths.interpolated_array")
    assert isinstance(paths, list)
    assert len(paths) == 3
    assert all(isinstance(path, Path) for path in paths)
    assert [str(path) for path in paths] == ["data/path1", "data/path2", "data/path3"]


def test_get_input_output_paths(sample_config_file):
    """Test getting input and output paths at the same level."""
    config = Config(sample_config_file)

    # Get input/output paths individually
    semianalysis_input = config.get_path("process.articles.semianalysis.input")
    semianalysis_output = config.get_path("process.articles.semianalysis.output")
    assert isinstance(semianalysis_input, Path)
    assert isinstance(semianalysis_output, Path)
    assert str(semianalysis_input) == "data/semianalysis.jsonl"
    assert str(semianalysis_output) == "data/processed_semianalysis.jsonl"

    # Get input/output paths from a different section
    kg_raw_input = config.get_path("process.kg.raw.input")
    kg_raw_output = config.get_path("process.kg.raw.output")
    assert isinstance(kg_raw_input, list)
    assert all(isinstance(path, Path) for path in kg_raw_input)
    assert [str(path) for path in kg_raw_input] == [
        "data/processed_semianalysis.jsonl",
        "data/processed_theinformation.jsonl",
    ]
    assert isinstance(kg_raw_output, Path)
    assert str(kg_raw_output) == "data/knowledge_graph"

    # Get array inputs as paths
    kg_array_inputs = config.get_path("process.kg.raw.array_inputs")
    assert isinstance(kg_array_inputs, list)
    assert all(isinstance(path, Path) for path in kg_array_inputs)
    assert [str(path) for path in kg_array_inputs] == ["data/input1.jsonl", "data/input2.jsonl"]


def test_reload(sample_config_file):
    """Test reloading the configuration file."""
    config = Config(sample_config_file)
    original_value = config.get("test.value")

    # Modify the configuration file
    with open(sample_config_file, "a") as f:
        f.write(
            "\n            # Added value\n            test:\n              value: 'modified_value'\n"
        )

    # Reload the configuration
    config.reload()

    # The value should now be updated
    assert config.get("test.value") != original_value


def test_file_not_found():
    """Test FileNotFoundError is raised for non-existent config file."""
    with pytest.raises(FileNotFoundError):
        Config("non_existent_file.yml")
