# Pre-commit Setup

This project uses [pre-commit](https://pre-commit.com/) to run linters and formatters automatically before each commit.

## Initial Setup

After cloning the repository, install the pre-commit hooks:

```bash
# Install pre-commit (if using the Python virtual environment)
cd api
pip install -r requirements.txt

# Install the git hooks
cd ..
pre-commit install
```

## What Gets Checked

The pre-commit hooks will automatically run:

### For Python files (`api/`)
- **Ruff** - Fast Python linter and formatter (replaces flake8, black, isort)
- **mypy** - Static type checker

### For TypeScript/JavaScript files (`web/`)
- **ESLint** - Linting and code style enforcement

### General
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Large file checks
- Merge conflict detection

## Running Manually

You can run pre-commit checks manually:

```bash
# Run on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files path/to/file.py

# Run a specific hook
pre-commit run ruff --all-files
```

## Skipping Hooks (Not Recommended)

If you absolutely need to commit without running the hooks:

```bash
git commit --no-verify
```

**Note:** This is discouraged as it bypasses quality checks.

## Updating Hooks

To update the pre-commit hooks to the latest versions:

```bash
pre-commit autoupdate
```
