#!/bin/bash
###############################################################################
# PS3 Emulator Auto-Config - Utility Functions
# Use directly: bash scripts/utilities.sh
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PS3_IP="${PS3_IP:-192.168.1.100}"
PS3_USER="${PS3_USER:-root}"

ps3_exec() {
    local cmd="$1"
    local description="${2:-Running command}"

    echo -e "${BLUE}ℹ${NC} $description..."
    if output=$(ssh -o ConnectTimeout=5 "${PS3_USER}@${PS3_IP}" "$cmd" 2>&1); then
        echo -e "${GREEN}✓${NC} Success"
        [ -n "$output" ] && echo "$output"
        return 0
    else
        echo -e "${RED}✗${NC} Error"
        return 1
    fi
}

ps3_copy() {
    local source="$1"
    local dest="$2"
    local description="${3:-Uploading file}"

    echo -e "${BLUE}ℹ${NC} $description..."

    if [ ! -f "$source" ]; then
        echo -e "${RED}✗${NC} File not found: $source"
        return 1
    fi

    if scp -q "$source" "${PS3_USER}@${PS3_IP}:${dest}" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Uploaded to $dest"
        return 0
    else
        echo -e "${RED}✗${NC} Upload failed"
        return 1
    fi
}

ps3_list_vmcs() {
    echo ""
    echo -e "${BLUE}Memory Cards on PS3:${NC}"
    ps3_exec "ls -lh /dev_hdd0/vmc/*.vmc 2>/dev/null | awk '{print \"  \" \$9 \" (\" \$5 \")\"}'" "Listing VMC files"
    echo ""
}

ps3_create_vmc() {
    local name="$1"
    local size="${2:-128}"

    if [ -z "$name" ]; then
        echo -e "${RED}✗${NC} Usage: ps3_create_vmc <name> [size_mb]"
        return 1
    fi

    ps3_exec "dd if=/dev/zero of=/dev_hdd0/vmc/$name bs=1M count=$size 2>/dev/null && chmod 666 /dev_hdd0/vmc/$name" \
        "Creating memory card $name (${size}MB)"
}

ps3_backup_vmc() {
    local vmc_name="$1"
    local backup_dir="${2:-.}"

    if [ -z "$vmc_name" ]; then
        echo -e "${RED}✗${NC} Usage: ps3_backup_vmc <vmc_name> [backup_dir]"
        return 1
    fi

    echo -e "${BLUE}ℹ${NC} Backing up $vmc_name..."
    if scp -q "${PS3_USER}@${PS3_IP}:/dev_hdd0/vmc/$vmc_name" "$backup_dir/" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Backup saved: $backup_dir/$vmc_name"
        return 0
    else
        echo -e "${RED}✗${NC} Backup failed"
        return 1
    fi
}

ps3_restore_vmc() {
    local backup_file="$1"
    local vmc_name="${2:-$(basename "$backup_file")}"

    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        echo -e "${RED}✗${NC} Usage: ps3_restore_vmc <backup_file> [vmc_name]"
        return 1
    fi

    echo -e "${YELLOW}⚠${NC} This will overwrite /dev_hdd0/vmc/$vmc_name"
    read -r -p "Continue? (y/N): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Cancelled"
        return 1
    fi

    ps3_copy "$backup_file" "/dev_hdd0/vmc/$vmc_name" "Restoring memory card"
    ps3_exec "chmod 666 /dev_hdd0/vmc/$vmc_name" "Fixing permissions"
}

ps3_list_games() {
    local console="${1:-all}"

    echo ""
    if [ "$console" = "all" ] || [ "$console" = "ps1" ]; then
        echo -e "${BLUE}PS1 Games:${NC}"
        ps3_exec "ls /dev_hdd0/PSXISO/ 2>/dev/null | grep -E '\\.(iso|dec|bin)$' | head -10" "Listing PS1 ISOs" || echo "  (none)"
    fi

    if [ "$console" = "all" ] || [ "$console" = "ps2" ]; then
        echo -e "${BLUE}PS2 Games:${NC}"
        ps3_exec "ls /dev_hdd0/PS2ISO/ 2>/dev/null | grep -E '\\.(iso|dec|bin)$' | head -10" "Listing PS2 ISOs" || echo "  (none)"
    fi
    echo ""
}

ps3_check_connection() {
    echo -e "${BLUE}Testing PS3 connection...${NC}"
    if ssh -o ConnectTimeout=5 "${PS3_USER}@${PS3_IP}" "echo OK" 2>/dev/null | grep -q "OK"; then
        echo -e "${GREEN}✓${NC} Connected to ${PS3_IP}"
        return 0
    fi

    echo -e "${RED}✗${NC} Could not connect to ${PS3_IP}"
    echo "  Check SSH is enabled on PS3 and the IP is correct"
    return 1
}

ps3_status() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}PS3 EMULATOR STATUS${NC}"
    echo -e "${BLUE}========================================${NC}"

    ps3_check_connection || return 1
    ps3_list_vmcs

    echo -e "${BLUE}Installed scripts:${NC}"
    ps3_exec "ls -1 /dev_hdd0/ps3tweaks/*.sh 2>/dev/null | xargs -I {} basename {}" "Checking script files"

    echo -e "${BLUE}Recent log lines:${NC}"
    ps3_exec "tail -5 /dev_hdd0/ps3tweaks/launcher.log 2>/dev/null" "Reading log"

    echo -e "${BLUE}========================================${NC}"
}

ps3_log() {
    echo -e "${BLUE}Execution log:${NC}"
    ps3_exec "cat /dev_hdd0/ps3tweaks/launcher.log" "Reading full log"
}

ps3_log_clear() {
    echo -e "${YELLOW}⚠${NC} This will clear launcher.log"
    read -r -p "Continue? (y/N): " confirm
    if [ "$confirm" = "y" ]; then
        ps3_exec "rm /dev_hdd0/ps3tweaks/launcher.log && touch /dev_hdd0/ps3tweaks/launcher.log" "Clearing log"
    fi
}

show_menu() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}PS3 EMU AUTO-CONFIG - Utilities${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo "Connection:"
    echo "  1. Test PS3 connection"
    echo "  2. Show overall status"
    echo ""
    echo "Memory Cards:"
    echo "  3. List memory cards"
    echo "  4. Create memory card"
    echo "  5. Backup memory card"
    echo "  6. Restore memory card"
    echo ""
    echo "Games:"
    echo "  7. List games (PS1/PS2)"
    echo ""
    echo "Logs:"
    echo "  8. View log"
    echo "  9. Clear log"
    echo ""
    echo "  0. Exit"
    echo -e "${BLUE}========================================${NC}"
}

interactive_menu() {
    while true; do
        show_menu
        read -r -p "Choose an option: " choice

        case $choice in
            1) ps3_check_connection ;;
            2) ps3_status ;;
            3) ps3_list_vmcs ;;
            4)
                read -r -p "Memory card name: " name
                ps3_create_vmc "$name"
                ;;
            5)
                read -r -p "Memory card name to backup: " vmc
                ps3_backup_vmc "$vmc"
                ;;
            6)
                read -r -p "Backup file path: " backup
                read -r -p "Destination VMC name on PS3: " name
                ps3_restore_vmc "$backup" "$name"
                ;;
            7)
                read -r -p "Console (ps1/ps2/all): " console
                ps3_list_games "$console"
                ;;
            8) ps3_log ;;
            9) ps3_log_clear ;;
            0) echo "Exiting..."; exit 0 ;;
            *) echo -e "${RED}✗${NC} Invalid option" ;;
        esac

        read -r -p "Press ENTER to continue..."
    done
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    interactive_menu
fi
