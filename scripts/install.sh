#!/bin/bash
###############################################################################
# PS3 Emulator Auto-Config - Installation Script
# Usage: bash scripts/install.sh <ps3_ip>
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}=====================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=====================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

PS3_IP="${1:-}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -z "$PS3_IP" ]; then
    print_error "Usage: bash scripts/install.sh <ps3_ip>"
fi

print_header "PS3 Emulator Auto-Config Installer"
print_info "PS3 IP: $PS3_IP"

print_info "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 "root@$PS3_IP" "echo OK" 2>/dev/null | grep -q OK; then
    print_error "Could not connect to PS3 via SSH"
fi
print_success "SSH connection OK"

print_info "Creating directories on PS3..."
ssh "root@$PS3_IP" << 'EOF'
mkdir -p /dev_hdd0/ps3tweaks
mkdir -p /dev_hdd0/vmc
chmod 777 /dev_hdd0/ps3tweaks
chmod 777 /dev_hdd0/vmc
EOF
print_success "Directories created"

print_info "Backing up emulator binaries..."
ssh "root@$PS3_IP" << 'EOF'
if [ -f /usr/lib64/ps1_netemu.self ] && [ ! -f /dev_hdd0/ps3tweaks/ps1_netemu.self.bak ]; then
    cp /usr/lib64/ps1_netemu.self /dev_hdd0/ps3tweaks/ps1_netemu.self.bak
fi
if [ -f /usr/lib64/ps2_netemu.self ] && [ ! -f /dev_hdd0/ps3tweaks/ps2_netemu.self.bak ]; then
    cp /usr/lib64/ps2_netemu.self /dev_hdd0/ps3tweaks/ps2_netemu.self.bak
fi
EOF
print_success "Backups ready"

print_info "Uploading integration script..."
scp "$SCRIPT_DIR/webman_integration.sh" "root@$PS3_IP:/dev_hdd0/ps3tweaks/" 2>/dev/null || print_error "Failed to upload webman_integration.sh"
ssh "root@$PS3_IP" "chmod +x /dev_hdd0/ps3tweaks/webman_integration.sh"
print_success "Integration script uploaded"

print_info "Checking memory cards..."
ssh "root@$PS3_IP" << 'EOF'
if [ ! -f /dev_hdd0/vmc/PS1_slot1.vmc ]; then
    dd if=/dev/zero of=/dev_hdd0/vmc/PS1_slot1.vmc bs=1M count=128 2>/dev/null
fi
if [ ! -f /dev_hdd0/vmc/PS2_slot1.vmc ]; then
    dd if=/dev/zero of=/dev_hdd0/vmc/PS2_slot1.vmc bs=1M count=128 2>/dev/null
fi
chmod 666 /dev_hdd0/vmc/*.vmc 2>/dev/null || true
EOF
print_success "Memory cards ready"

print_info "Generating launcher scripts..."
cat > /tmp/launcher_ps1.sh << 'EOF'
#!/bin/bash
/dev_hdd0/ps3tweaks/webman_integration.sh "${1:-/dev_hdd0/PSXISO/AUTO.ISO}"
exec /dev_hdd0/ps3tweaks/ps1_netemu.self.bak "$@"
EOF

cat > /tmp/launcher_ps2.sh << 'EOF'
#!/bin/bash
/dev_hdd0/ps3tweaks/webman_integration.sh "${1:-/dev_hdd0/PS2ISO/AUTO.ISO}"
exec /dev_hdd0/ps3tweaks/ps2_netemu.self.bak "$@"
EOF

chmod +x /tmp/launcher_ps1.sh /tmp/launcher_ps2.sh
scp /tmp/launcher_ps1.sh "root@$PS3_IP:/dev_hdd0/ps3tweaks/" 2>/dev/null
scp /tmp/launcher_ps2.sh "root@$PS3_IP:/dev_hdd0/ps3tweaks/" 2>/dev/null
ssh "root@$PS3_IP" "chmod +x /dev_hdd0/ps3tweaks/launcher_*.sh"
rm /tmp/launcher_*.sh
print_success "Launcher scripts created"

print_header "Installation Complete"
print_info "PS3 path: /dev_hdd0/ps3tweaks"
print_info "Log file: /dev_hdd0/ps3tweaks/launcher.log"
print_info "Next: run 'bash scripts/utilities.sh' for diagnostics"

print_success "Done"
