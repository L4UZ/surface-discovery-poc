# Quick Setup Guide

## Auto-Activation Setup (Recommended)

The project now automatically activates the virtual environment when you `cd` into the directory using `direnv`.

### First Time Setup

```bash
# 1. Reload your shell to enable direnv
source ~/.zshrc

# 2. Allow direnv for this project (one-time only)
cd /path/to/surface-discovery
direnv allow .
```

### What Happens

When you enter the directory:
```bash
cd surface-discovery
# direnv: loading ~/repos/surface-discovery/.envrc
# direnv: export +VIRTUAL_ENV ~PATH
```

The virtual environment is now active! No need for `source .venv/bin/activate` or `uv run`.

```bash
# Just use python directly
python cli.py --url example.com

# Or run tests
pytest tests/
```

When you leave the directory, it automatically deactivates.

## Manual Activation (Alternative)

If you prefer manual control:

```bash
# Activate
source .venv/bin/activate

# Use normally
python cli.py --url example.com

# Deactivate when done
deactivate
```

## Using uv run (No Activation Needed)

You can always use `uv run` without activating:

```bash
uv run python cli.py --url example.com
uv run pytest tests/
```

## Custom Environment Variables

Edit `.envrc` to add project-specific environment variables:

```bash
# Add to .envrc
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development
export API_TOKEN=your_token
```

Then reload:
```bash
direnv allow .
```

## Troubleshooting

### direnv not working?

1. Check if direnv hook is in your shell config:
   ```bash
   grep 'direnv hook' ~/.zshrc
   ```

2. If not found, add it:
   ```bash
   echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
   source ~/.zshrc
   ```

3. Allow the directory:
   ```bash
   direnv allow .
   ```

### Want to disable auto-activation?

```bash
# Temporarily disable for this session
direnv deny .

# Re-enable later
direnv allow .
```

### Check direnv status

```bash
direnv status
```
