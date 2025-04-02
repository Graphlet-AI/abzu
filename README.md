# Abzu

Waters of wisdom... knowledge graph of silicon.

## Project Setup

```bash
conda create -n abzu python=3.12 -y
conda activate abzu

poetry install

# black, isort, flake8, mypy
pre-commit install

# To rebuild abzu.baml_client
baml-cli generate
```

## Crawl

Crawl SemiAnalysis.com via:

```bash
python abzu/crawl.py
```

## Information Extraction

Run the information extracton via:

```bash

```
