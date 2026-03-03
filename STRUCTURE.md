# Project Structure

```text
ps3tweaks/
├── README.md
├── Makefile
├── pyproject.toml
├── uv.lock
├── src/
│   └── ps3tweaks/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── manager.py
│       └── utils.py
├── scripts/
│   ├── install.sh
│   ├── utilities.sh
│   └── webman_integration.sh
├── docs/
│   ├── README.md
│   ├── QUICKSTART.md
│   └── UV_SETUP.md
├── config/
│   └── ps3_emulator_config.example.json
├── tools/
│   ├── dev_env.sh
│   └── download_covers.py
└── tests/
    └── test_config.py
```

## Purpose by Folder

- `src/`: main Python package
- `scripts/`: PS3 integration and install scripts
- `docs/`: user and setup docs
- `config/`: sample/default configuration
- `tools/`: local helper utilities
- `tests/`: unit tests
