# dev-tool

Local VM and project manager for containerized development.

**dev** manages a Lima VM on macOS with Podman inside for running containerized development environments.

## Installation

### Quick install

```bash
curl -sSL https://raw.githubusercontent.com/k4zzzz/sandboxed-dev-tool/refs/heads/main/install.sh | bash
```

Then restart your terminal or run `source ~/.zshrc` (or `~/.bash_profile`).

### Manual install

Requires: Lima, Podman, Git

```bash
# Install dependencies
brew install lima uv

# Clone and install
git clone https://github.com/k4zzzz/sandboxed-dev-tool
cd sandboxed-dev-tool
uv tool install . --force

# Add uv bin to PATH
export PATH="$(uv tool bin):$PATH"
```

## Usage

### VM Commands (run on macOS)

| Command | Description |
|---------|-------------|
| `dev vm create` | Provision a fresh VM (deletes existing if any) |
| `dev vm start` | Start the VM |
| `dev vm stop` | Stop the VM |
| `dev vm delete` | Stop and permanently delete the VM |

### Project Commands (run inside VM)

| Command | Description |
|---------|-------------|
| `dev project new <path> -t <template>` | Create a new project from a template |
| `dev project start <path>` | Start project's containers |
| `dev project stop <path>` | Stop project's containers |
| `dev project shell <path>` | Open shell in running container |
| `dev project list` | List running containers |
| `dev project delete <path>` | Stop, remove volumes, delete project |

### Examples

```bash
# Create and start a new project
dev project new ~/myapp -t python
dev project shell ~/myapp

# Stop when done
dev project stop ~/myapp

# Start again later
dev project start ~/myapp
```

## Requirements

- macOS (for Lima VM)
- Linux inside VM (Podman)