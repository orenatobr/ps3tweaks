# Quick Start - PS3 Emulator Auto-Config

## 1) Prepare your host

```bash
cd ~/Workspace/ps3tweaks
source tools/dev_env.sh
```

## 2) Enable SSH on PS3

- XMB → Dev Tools → SSH Server → ON
- Check PS3 IP in network settings

## 3) Install runtime scripts to PS3

```bash
bash scripts/install.sh 192.168.1.100
```

## 4) Validate setup

```bash
bash scripts/utilities.sh
```

## 5) Run the interactive manager

```bash
ps3-config
```

## Common Checks

```bash
ssh root@192.168.1.100 "ls -la /dev_hdd0/ps3tweaks"
ssh root@192.168.1.100 "ls -lh /dev_hdd0/vmc"
ssh root@192.168.1.100 "tail -20 /dev_hdd0/ps3tweaks/launcher.log"
```

## Expected Result

- PS1 launches with analog mode + normal screen + PS1 VMC slot 1
- PS2 launches with fullscreen + PS2 VMC slot 1
