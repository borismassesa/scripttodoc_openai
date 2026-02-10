# Test Output Directory

This directory contains test results and sample outputs from the ScriptToDoc pipeline.

## Structure

- `sample_results/` - Example outputs from end-to-end tests
  - Phase 1 and Phase 2 test results
  - Sample generated documents
  - Pipeline metrics and analysis

## Usage

Test outputs are automatically generated when running:
```bash
pytest tests/e2e/
```

## Note

This directory is excluded from version control via .gitignore. Only sample results are committed for documentation purposes.
