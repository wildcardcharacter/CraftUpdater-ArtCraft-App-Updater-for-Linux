#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VERSION=${1:-0.2.0}

case "$VERSION" in
  ""|*[!A-Za-z0-9.+~:-]*)
    printf 'Invalid Debian package version: %s\n' "$VERSION" >&2
    exit 2
    ;;
esac

if ! command -v dpkg-deb >/dev/null 2>&1; then
  printf 'dpkg-deb is required to build the package.\n' >&2
  exit 1
fi

TEMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/craft-updater-deb.XXXXXX")
trap 'rm -rf "$TEMP_DIR"' EXIT HUP INT TERM
PACKAGE_DIR="$TEMP_DIR/package"

install -Dm755 "$ROOT_DIR/craft_updater.py" "$PACKAGE_DIR/usr/bin/craft-updater"
install -Dm644 "$ROOT_DIR/packaging/debian/craft-updater.desktop" \
  "$PACKAGE_DIR/usr/share/applications/craft-updater.desktop"
install -Dm644 "$ROOT_DIR/assets/icons/craft-updater.svg" \
  "$PACKAGE_DIR/usr/share/icons/hicolor/scalable/apps/craft-updater.svg"

mkdir -p "$PACKAGE_DIR/DEBIAN" "$ROOT_DIR/dist"
sed "s/@VERSION@/$VERSION/" "$ROOT_DIR/packaging/debian/control.in" \
  > "$PACKAGE_DIR/DEBIAN/control"

OUTPUT="$ROOT_DIR/dist/craft-updater_${VERSION}_all.deb"
dpkg-deb --root-owner-group --build "$PACKAGE_DIR" "$OUTPUT"
printf 'Built package: %s\n' "$OUTPUT"
