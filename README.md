# PS3 Tweaks - Emulator Auto-Config

Automatic setup for PS1/PS2 emulator behavior on PS3 CFW (Evilnat 4.92.2):

- PS1: analog mode, normal screen mode, PS1 memory card in slot 1
- PS2: fullscreen mode, PS2 memory card in slot 1

## Quick Start

```bash
source tools/dev_env.sh
bash scripts/install.sh 192.168.1.100
ps3-config
```

## Project Layout

- `src/ps3tweaks/` - Python package (`cli`, manager, models, utilities)
- `scripts/` - PS3 install/integration shell scripts
- `docs/` - detailed documentation
- `config/` - config templates and local config
- `tools/` - local helpers
- `tests/` - unit tests

## Main Commands

```bash
make setup
make test
make lint
make format
make install-ps3
```

## Documentation

- [Full Docs](docs/README.md)
- [Quick Start](docs/QUICKSTART.md)
- [UV Environment Setup](docs/UV_SETUP.md)

## Compatibility

- PS3 CFW: Evilnat 4.92.2+
- Python: 3.8+
- Platform: macOS/Linux (for host scripts)
