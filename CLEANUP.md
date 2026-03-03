# Cleanup Summary

## What changed

- Standardized all project text to English
- Reorganized runtime and host scripts by responsibility
- Centralized package code in `src/ps3tweaks`
- Simplified and updated documentation
- Fixed script path issues after reorganization

## Key fixes

- `tools/dev_env.sh` now resolves project root correctly
- `scripts/install.sh` now uses a valid `SCRIPT_DIR`
- CLI and manager messages are fully English
- Build/dev commands in `Makefile` are fully English

## Current status

The project is now consistent, cleaner, and easier to maintain.
