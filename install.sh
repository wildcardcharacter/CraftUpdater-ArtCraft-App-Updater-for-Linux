#!/bin/sh
set -eu

BASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN_DIR="${HOME}/.local/bin"
APPS_DIR="${HOME}/.local/share/applications"
mkdir -p "$BIN_DIR" "$APPS_DIR"
ln -sf "$BASE_DIR/craft_updater.py" "$BIN_DIR/craft-updater"
EXEC_PATH=$(printf '%s' "$BIN_DIR/craft-updater" | sed 's/\\/\\\\/g; s/"/\\"/g')
cat > "$APPS_DIR/craft-updater.desktop" <<EOF
[Desktop Entry]
Name=CraftUpdater
Comment=ArtCraft-Apps aktualisieren
Exec="$EXEC_PATH"
Terminal=false
Type=Application
Categories=Utility;
EOF
chmod +x "$BASE_DIR/craft_updater.py"
printf 'CraftUpdater wurde installiert. Starte es mit: %s/craft-updater\n' "$BIN_DIR"
