# Abzu

A Knowledge Graph Bloomberg Terminal™ + Waters of wisdom... knowledge graph of silicon.

## Project Setup

```bash
conda create -n abzu python=3.12 -y
conda activate abzu

#
# Install poetry
#
# conda install -c conda-forge poetry
#
poetry install

# black, isort, flake8, mypy
pre-commit install

# To rebuild abzu.baml_client
# NOTE: make sure your plugin and baml-py versions match!
baml-cli generate
```

## Crawl

Crawl SemiAnalysis.com via:

```bash
python abzu/crawl.py
```

## Information Extraction

Run the information extracton via the [VSCode Plugin](https://marketplace.visualstudio.com/items?itemName=Boundary.baml-extension):

```bash
baml-cli generate

# To run the test data
baml-cli test
```
