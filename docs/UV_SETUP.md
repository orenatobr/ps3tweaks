# UV Environment Setup

## Create and activate environment

```bash
cd ~/Workspace/ps3tweaks
uv venv
source .venv/bin/activate
uv pip install -e .[dev]
```

Or use the helper:

```bash
source tools/dev_env.sh
```

## Verify packages

```bash
python -c "import paramiko, requests, PIL; print('OK')"
pytest --version
black --version
flake8 --version
```

## Daily workflow

```bash
source tools/dev_env.sh
make test
make lint
```

## Deactivate

```bash
deactivate
```
