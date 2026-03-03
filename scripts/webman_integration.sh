#!/bin/bash
###############################################################################
# PS3 Webman Integration Script
# Place this file at /dev_hdd0/ps3tweaks/webman_integration.sh
###############################################################################

set -e

PS3TWEAKS_DIR="/dev_hdd0/ps3tweaks"
VMC_PATH="/dev_hdd0/vmc"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$PS3TWEAKS_DIR/launcher.log"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1" | tee -a "$PS3TWEAKS_DIR/launcher.log"
}

log_error() {
    echo -e "${RED}[ERR]${NC} $1" | tee -a "$PS3TWEAKS_DIR/launcher.log"
}

log_config() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $1" >> "$PS3TWEAKS_DIR/launcher.log"
}

ensure_directories() {
    mkdir -p "$PS3TWEAKS_DIR"
    mkdir -p "$VMC_PATH"
    touch "$PS3TWEAKS_DIR/launcher.log"
}

get_game_type() {
    local iso_path="$1"

    if [[ "$iso_path" == *"PSXISO"* ]]; then
        echo "ps1"
    elif [[ "$iso_path" == *"PS2ISO"* ]]; then
        echo "ps2"
    else
        echo "unknown"
    fi
}

setup_memory_card() {
    local console="$1"

    log_info "Configuring memory card for $console"

    case "$console" in
        ps1)
            vmc_file="PS1_slot1.vmc"
            ;;
        ps2)
            vmc_file="PS2_slot1.vmc"
            ;;
        *)
            log_error "Unknown console: $console"
            return 1
            ;;
    esac

    vmc_source="$VMC_PATH/$vmc_file"

    if [ ! -f "$vmc_source" ]; then
        log_info "Creating missing memory card: $vmc_file"
        dd if=/dev/zero of="$vmc_source" bs=1M count=128 2>/dev/null || {
            log_error "Failed to create memory card"
            return 1
        }
    fi

    ln -sf "$vmc_source" "$VMC_PATH/slot1.vmc" 2>/dev/null || true
    log_success "Memory card set: $vmc_file"
    log_config "MEM_CARD_SLOT1=$vmc_file"
    return 0
}

setup_video_mode() {
    local console="$1"
    local mode="normal"

    if [ "$console" = "ps2" ]; then
        mode="fullscreen"
    fi

    log_info "Setting video mode: $mode"
    log_config "VIDEO_MODE=$mode"
    return 0
}

setup_input_mode() {
    local console="$1"

    if [ "$console" = "ps1" ]; then
        log_info "Enabling analog mode for PS1"
        log_config "INPUT_MODE=analog"
    fi

    return 0
}

main() {
    local iso_path="${1:-}"

    if [ -z "$iso_path" ]; then
        log_error "Usage: $0 <iso_path>"
        exit 1
    fi

    ensure_directories

    log_info "=========================================="
    log_info "PS3 Emulator Auto-Config Launcher"
    log_info "=========================================="
    log_info "ISO: $iso_path"

    console=$(get_game_type "$iso_path")
    if [ "$console" = "unknown" ]; then
        log_error "Could not detect console type from ISO path"
        log_error "Expected /dev_hdd0/PSXISO/ or /dev_hdd0/PS2ISO/"
        exit 1
    fi

    log_success "Detected console: $console"

    setup_memory_card "$console" || { log_error "Memory card setup failed"; exit 1; }
    setup_video_mode "$console" || { log_error "Video setup failed"; exit 1; }
    setup_input_mode "$console" || { log_error "Input setup failed"; exit 1; }

    log_success "All settings applied"
    log_info "=========================================="
}

main "$@"
exit $?
