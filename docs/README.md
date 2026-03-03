# PS3 Emulator Auto-Config Documentation

This project prepares PS3 emulator settings before launching PS1/PS2 content.

## Behavior by Emulator

### PS1 (`ps1_netemu.self`)

- Enables analog mode
- Uses normal screen mode
- Maps PS1 VMC to slot 1

### PS2 (`ps2_netemu.self`)

- Uses fullscreen mode
- Maps PS2 VMC to slot 1

## Components

### Python CLI

- Entry command: `ps3-config`
- Source: `src/ps3tweaks/`
- Features:
  - Connect to PS3 over SSH
  - List VMC files and games
  - Save per-game settings
  - Upload launcher scripts

### Shell Integration

- `scripts/install.sh`: installs runtime scripts to PS3
- `scripts/webman_integration.sh`: applies runtime settings
- `scripts/utilities.sh`: diagnostics and maintenance helpers

## Installation

### 1) Host setup

```bash
cd ~/Workspace/ps3tweaks
source tools/dev_env.sh
```

### 2) Install on PS3

```bash
bash scripts/install.sh 192.168.1.100
```

### 3) Verify

```bash
bash scripts/utilities.sh
```

## PS3 Paths Used

- Runtime scripts: `/dev_hdd0/ps3tweaks/`
- VMC files: `/dev_hdd0/vmc/`
- PS1 ISOs: `/dev_hdd0/PSXISO/`
- PS2 ISOs: `/dev_hdd0/PS2ISO/`

## Memory Card Defaults

- `PS1_slot1.vmc`
- `PS2_slot1.vmc`

If missing, scripts create them as 128 MB files.

## Troubleshooting

### SSH connection fails

- Confirm SSH is enabled in CFW settings
- Confirm PS3 IP address
- Confirm network reachability (port 22)

### VMC not applied

- Confirm file exists in `/dev_hdd0/vmc/`
- Check `launcher.log` under `/dev_hdd0/ps3tweaks/`

### Permissions issues

```bash
ssh root@<PS3_IP> "chmod +x /dev_hdd0/ps3tweaks/*.sh && chmod 666 /dev_hdd0/vmc/*.vmc"
```

## Notes

- This project does not patch Sony emulator binaries automatically.
- It focuses on pre-launch setup and consistent runtime behavior.
