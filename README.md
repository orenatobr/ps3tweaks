# PS3 Emulator Auto-Config

**Automatic PS1/PS2 emulator configuration manager for PlayStation 3 Custom Firmware (CFW).**

Auto-configures memory cards, video modes, and input settings before launching PS1/PS2 games on PS3 Evilnat CFW 4.92.2+ via SSH.

## 🎯 Purpose

Simplify PS1/PS2 emulator behavior configuration on PS3 by:
- Pre-setting analog/digital input modes per console
- Configuring video modes (normal/full-screen)
- Mapping virtual memory cards to emulator slots
- Persisting game-specific settings in JSON
- Generating and deploying launcher scripts via SSH

### Why?

PS3 emulators (`ps1_netemu.self`, `ps2_netemu.self`) require careful setup for optimal compatibility. This tool eliminates manual configuration before each game session.

## 📋 Requirements

- **Hardware:** PlayStation 3 with Custom Firmware (Evilnat 4.92.2+)
- **Network:** SSH enabled on PS3 + accessible from your host
- **Host:** macOS, Linux, or WSL with Python 3.10+
- **Memory:** ~64 MB available on PS3 HDD for VMC files

## ⚡ Quick Start

### 1. Prepare Your Host

```bash
cd ~/Workspace/ps3tweaks
uv venv                              # Create virtual environment
source .venv/bin/activate            # Activate
uv pip install -e .[dev]             # Install package + dev tools
```

### 2. Enable SSH on PS3

- XMB → Dev Tools → SSH Server → ON
- Note PS3 IP from Network Settings

### 3. Deploy Runtime Scripts

```bash
bash scripts/install.sh 192.168.1.100
```

Installs launcher scripts and creates/initializes virtual memory cards.

### 4. Run Interactive Manager

```bash
ps3-config
```

Menu-driven interface for:
- Listing games and VMCs
- Configuring per-game settings
- Uploading launchers
- Checking connection status

### 5. Launch Games

Webman → Game → Automatic launcher applies settings before emulator launch

---

## 🏗️ Architecture

### Python Package (`src/ps3tweaks/`)

| Module | Role |
|--------|------|
| `config.py` | Emulator configuration dataclasses (PS1/PS2 defaults) |
| `utils.py` | SSH/SFTP client + JSON config persistence |
| `manager.py` | High-level orchestration (list/configure/upload) |
| `cli.py` | Interactive menu interface |

### Shell Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `install.sh` | Deploy to PS3, create VMC files, upload launchers |
| `webman_integration.sh` | Runtime hook: pre-launch setup |
| `utilities.sh` | Diagnostics, VMC backup/restore, log viewing |

### Tools (`tools/`)

| Tool | Purpose |
|------|---------|
| `download_covers.py` | Download game covers from TheGamesDB/RetroArch |
| `dev_env.sh` | Virtual environment activation helper |

## 📝 Configuration

### Default Emulator Settings

**PS1 (`ps1_netemu.self`):**
- Analog mode: **enabled**
- Video mode: **normal**
- Memory card: `PS1_slot1.vmc`

**PS2 (`ps2_netemu.self`):**
- Analog mode: **disabled**
- Video mode: **fullscreen**
- Memory card: `PS2_slot1.vmc`

### Per-Game Overrides

Configuration stored in `config/ps3_emulator_config.json`:

```json
{
  "games": {
    "Metal Gear Solid": {
      "console": "ps1",
      "memory_card_slot1": "PS1_slot1.vmc",
      "video_mode": "normal",
      "analog_mode": true
    }
  }
}
```

## 🔧 Development

### Project Structure

```
ps3tweaks/
├── .github/
│   └── copilot-instructions.md      # Engineering standards
├── .pre-commit-config.yaml          # Linting hooks
├── src/ps3tweaks/                   # Main package
├── tests/                           # Unit + integration tests
├── scripts/                         # Deployment scripts
├── tools/                           # Utilities
├── config/                          # Configuration templates
└── docs/                            # Documentation
```

### Code Quality

All code follows **strict engineering standards**:

- ✅ **Type hints** on 100% of functions (Python 3.10+)
- ✅ **Google-style docstrings** for all public/private functions
- ✅ **Comprehensive logging** (DEBUG, INFO, WARNING, ERROR)
- ✅ **Unit + integration tests** (82%+ coverage)
- ✅ **Automated formatting** (isort, black, ruff, flake8)

### Running Tests

```bash
pytest --cov=src/ps3tweaks --cov-report=term-missing
```

Requires 80%+ coverage.

### Pre-commit Hooks

```bash
pre-commit run -a
```

Enforces:
- Python AST validation
- Import sorting (isort)
- Code formatting (black)
- Linting (ruff, flake8)
- Test coverage gates

---

## 📚 Documentation

- [**QUICKSTART.md**](docs/QUICKSTART.md) — Step-by-step setup guide
- [**docs/README.md**](docs/README.md) — Component overview
- [**UV_SETUP.md**](docs/UV_SETUP.md) — Virtual environment setup
- [**STRUCTURE.md**](STRUCTURE.md) — Project organization details

## 🚀 Deployment

### Host → PS3 Workflow

1. **User runs `ps3-config`** on host machine
2. **Manager connects via SSH** to PS3
3. **Lists** available VMCs and games
4. **Stores** game-specific settings in JSON
5. **Generates** launcher scripts
6. **Uploads** via SFTP to `/dev_hdd0/ps3tweaks/`
7. **Webman launcher** invokes scripts on game launch

### Runtime Flow (PS3)

```
Webman Launch → /dev_hdd0/ps3tweaks/launcher_ps1.sh
    ↓
webman_integration.sh (apply settings)
    ↓
Mount memory card
Set video mode
Set analog mode
    ↓
Executive ps1_netemu.self with game ISO
```

## 🔐 Security

- **No hardcoded credentials** in code
- **SSH key-based auth** supported (username + password fallback)
- **Files never logged** (only paths, which exclude secrets)
- **.gitignore** excludes config files with real credentials

## 🐛 Troubleshooting

### SSH Connection Fails
- Confirm SSH is enabled on PS3 (Dev Tools)
- Verify PS3 IP is reachable (`ping 192.168.1.100`)
- Check firewall allows SSH (port 22)

### VMCs Not Applied
- Verify files exist: `ls -la /dev_hdd0/vmc/`
- Check launcher logs: `cat /dev_hdd0/ps3tweaks/launcher.log`
- Permissions: `chmod 666 /dev_hdd0/vmc/*.vmc`

### Game-Specific Issues
- Review per-game config in `config/ps3_emulator_config.json`
- Reset to defaults by removing the game entry
- Rerun `ps3-config` to reconfigure

---

## 📄 License

This project is provided as-is for PS3 Custom Firmware enthusiasts.

## 🤝 Contributing

Improvements welcome! Ensure:
- All tests pass (`pytest`)
- Coverage ≥ 80%
- Code passes all linters (`pre-commit run -a`)
- Commit messages follow Conventional Commits
- Docstrings updated for public API changes

## 📞 Support

For issues or questions:
1. Check [QUICKSTART.md](docs/QUICKSTART.md) and [docs/README.md](docs/README.md)
2. Review troubleshooting section above
3. Open an issue with:
   - PS3 CFW version (e.g., Evilnat 4.92.2)
   - Error messages from logs
   - Steps to reproduce
