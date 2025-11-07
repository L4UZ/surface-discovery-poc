# Complete Installation & Setup Guide

## Quick Start (3 Steps)

```bash
# 1. Install external security tools
./scripts/install-tools.sh

# 2. Setup Python environment
uv sync

# 3. Enable auto-activation (optional)
brew install direnv && echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc && source ~/.zshrc
direnv allow .
```

Done! Your environment is ready.

---

## Part 1: External Tools Installation

### Automated Installation (Recommended)

```bash
./scripts/install-tools.sh
```

This installs all required ProjectDiscovery tools:
- **subfinder** - Subdomain enumeration
- **httpx** - HTTP probing
- **nuclei** - Vulnerability scanning
- **katana** - Web crawling
- **dnsx** - DNS resolution
- **naabu** - Port scanning

### Requirements

- **Go 1.20+** must be installed
- **macOS**: Script auto-detects Homebrew bash
- **Linux**: Works with system bash

### Manual Installation (Alternative)

If you prefer manual installation:

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

# Add to PATH
export PATH=$PATH:$HOME/go/bin
```

---

## Part 2: Python Environment Setup

### Using uv (Recommended)

```bash
# Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Run commands
uv run python cli.py --url example.com
```

### Benefits of uv:
- ⚡ 10-100x faster than pip
- 🔒 Reproducible builds with lockfile
- 🎯 No manual venv management
- 📦 Modern dependency resolution

### Using pip (Legacy)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Part 3: Auto-Activation Setup

Enable automatic virtual environment activation using `direnv`:

### Install direnv

```bash
# macOS
brew install direnv

# Linux (Ubuntu/Debian)
sudo apt install direnv

# Linux (Fedora/RHEL)
sudo dnf install direnv
```

### Configure your shell

```bash
# For zsh (macOS default)
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
source ~/.bashrc
```

### Enable for this project

```bash
direnv allow .
```

### How it works

When you enter the directory:
```bash
cd surface-discovery
# direnv: loading .envrc
# direnv: export +VIRTUAL_ENV ~PATH

# Virtual environment is active!
python cli.py --url example.com
```

Auto-deactivates when you leave.

---

## Verification

### Check installations

```bash
# External tools
subfinder -version
httpx -version
nuclei -version
katana -version
dnsx -version
naabu -version

# Python environment
python --version
which python  # Should show .venv/bin/python

# Run tests
pytest tests/
```

### Test the setup

```bash
# Quick reconnaissance scan
python cli.py --url example.com --depth shallow

# Check output
cat discovery_example_com.json
```

---

## Common Issues & Solutions

### "Go not found"

Install Go first:
```bash
# macOS
brew install go

# Linux
sudo apt-get install golang-go

# Verify
go version
```

### "Tools not found in PATH"

Add Go bin directory to PATH:
```bash
echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.zshrc
source ~/.zshrc
```

### "bash version too old" (macOS)

Install newer bash:
```bash
brew install bash
# Script will auto-detect and use it
```

### "direnv not activating"

1. Check if hook is installed:
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

### "Permission denied for naabu" (Linux)

Set network capabilities:
```bash
sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip $(which naabu)
```

---

## Custom Configuration

### Environment Variables

Edit `.envrc` to add project-specific variables:

```bash
# Add to .envrc
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development
export API_TOKEN=your_token
```

Reload:
```bash
direnv allow .
```

### Discovery Configuration

Edit `discovery/config.py` or use CLI flags:

```bash
python cli.py \
  --url example.com \
  --depth deep \
  --timeout 900 \
  --parallel 15 \
  --verbose
```

---

## Alternative Workflows

### Without direnv (manual activation)

```bash
source .venv/bin/activate
python cli.py --url example.com
deactivate
```

### With uv run (no activation needed)

```bash
uv run python cli.py --url example.com
uv run pytest tests/
```

### Docker (no local installation)

```bash
docker build -t surface-discovery .
docker run --rm -v $(pwd)/results:/output surface-discovery example.com
```

---

## Next Steps

1. ✅ Read [QUICKSTART.md](QUICKSTART.md) for usage examples
2. ✅ Check [AUTHENTICATED_SCAN.md](AUTHENTICATED_SCAN.md) for auth setup
3. ✅ Review [DOCKER.md](DOCKER.md) for containerized deployment
4. ✅ See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues

---

## Complete Example

```bash
# Full setup from scratch
cd ~/repos
git clone <repo-url>
cd surface-discovery

# 1. Install Go (if needed)
brew install go

# 2. Install external tools
./scripts/install-tools.sh

# 3. Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 4. Setup Python environment
uv sync

# 5. Setup auto-activation
brew install direnv
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc
direnv allow .

# 6. Test
cd .. && cd surface-discovery  # Trigger direnv
python cli.py --url example.com --depth shallow

# 7. Review results
cat discovery_example_com.json
```

Your environment is fully configured! 🎉
