#!/usr/bin/env python3
"""A small desktop frontend for building ArtCraft apps from source."""

from __future__ import annotations

import queue
import shutil
import subprocess
import threading
import configparser
import shlex
import os
import signal
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk


APPS = [
    ("PdfCraft", "pdfcraft"), ("WordCraft", "wordcraft"),
    ("GridCraft", "gridcraft"), ("DeckCraft", "deckcraft"),
    ("PhotoCraft", "photocraft"), ("LightCraft", "lightcraft"),
    ("VectorCraft", "vectorcraft"), ("DesignCraft", "designcraft"),
    ("CADCraft", "cadcraft"), ("SoundCraft", "soundcraft"),
    ("FilmCraft", "filmcraft"), ("EffectCraft", "effectcraft"),
]
HOME = Path.home()
APP_VERSION = "0.2.1"
GITHUB_REPO = "wildcardcharacter/CraftUpdater-ArtCraft-App-Updater-for-Linux"
REPOS = HOME / "git"
BIN_DIR = HOME / ".local" / "bin"
DATA_DIR = Path.home() / ".local" / "share"
LOG_FILE = Path.home() / ".local" / "state" / "craft-updater-gui" / "last-run.log"
BUILD_STATE_DIR = Path.home() / ".local" / "state" / "craft-updater-gui" / "builds"
SETTINGS_FILE = Path.home() / ".config" / "craft-updater-gui" / "settings.json"
DESKTOP_DIRS = (
    DATA_DIR / "applications",
    DATA_DIR / "flatpak" / "exports" / "share" / "applications",
    Path("/usr/local/share/applications"),
    Path("/usr/share/applications"),
    Path("/var/lib/flatpak/exports/share/applications"),
    Path("/var/lib/snapd/desktop/applications"),
)

TEXTS = {
    "de": {
        "subtitle": "Deine ArtCraft-Apps an einem Ort verwalten", "version_label": "Version {}", "language": "Sprache",
        "check": "Updates prüfen", "installed": "Installiert", "selected": "Ausgewählt",
        "sources": "Quellcode vorhanden", "apps": "Deine Apps", "search": "Suchen",
        "updates": "Updates offen", "app": "Anwendung", "status": "Status",
        "installed_version": "Installiert", "available_version": "Neueste Version", "commits": "Commits",
        "select_installed": "Installierte auswählen",
        "select_all": "Alle auswählen", "activity": "Aktivität", "clear": "Ansicht leeren",
        "ready": "Bereit", "force": "Neuaufbau erzwingen", "update_selected": "Ausgewählte aktualisieren",
        "none_title": "Keine Auswahl", "none_selected": "Bitte wähle mindestens eine App aus.",
        "check_run": "Updateprüfung", "update_run": "App-Update", "running": "{} läuft …",
        "command_failed": "Befehl fehlgeschlagen", "fetch": "Änderungen abrufen …",
        "clone": "Klonen: {}", "building": "{} wird gebaut (das kann einige Minuten dauern) …",
        "binary_missing": "Gebautes Programm nicht gefunden: {}",
        "already_current": "Bereits aktuell; kein Neuaufbau nötig.",
        "menu_installed": "Anwendungsmenü-Eintrag installiert: {}",
        "mime_installed": "Dateityp-Informationen installiert ({} XML-Datei(en)).",
        "no_desktop": "Kein passender Menüeintrag im Quellcode gefunden; installiert wurde nur das Programm.",
        "install_path": "Installiert: {}", "already_starts": "{}: Update startet",
        "app_completed": "{}: abgeschlossen", "checking_app": "{}: prüfe GitHub …",
        "waiting_clone": "Noch nicht geklont", "commits_waiting": "{} neue Commits", "up_to_date": "Aktuell",
        "installed_status": "Installiert · {}", "local": "Lokal", "system": "System",
        "source_status": "Quellcode vorhanden", "missing_status": "Nicht installiert",
        "failed": "Vorgang fehlgeschlagen", "error_title": "Vorgang fehlgeschlagen", "error_prefix": "FEHLER:",
        "unknown_version": "Unbekannt", "no_version": "—", "cancel": "Abbrechen",
        "cancelling": "Abbruch läuft …", "cancelled": "Abgebrochen", "close": "Schließen", "preflight": "Systemprüfung",
        "preflight_ok": "Voraussetzungen erfüllt; {} GB frei.",
        "missing_tools": "Benötigte Programme fehlen: {}. Installiere Git, Rust/Cargo, pkg-config und nice.",
        "missing_package": "Systembibliothek {} fehlt. Installiere das passende Entwicklungspaket.",
        "low_space": "Zu wenig freier Speicher: {} GB verfügbar, mindestens {} GB erforderlich.",
        "new_commits": "{} neue Commits", "version_check_failed": "Versionsprüfung fehlgeschlagen",
        "version_unknown": "Unbekannt",
        "update_complete_title": "Update abgeschlossen",
        "update_complete_message": "Der Update-Vorgang ist abgeschlossen.\n\nVerarbeitet: {}",
        "self_update": "CraftUpdater aktualisieren", "self_checking": "Prüfe CraftUpdater-Updates …",
        "self_current_title": "CraftUpdater ist aktuell", "self_current": "Du verwendest bereits CraftUpdater {}.",
        "self_available_title": "CraftUpdater-Update verfügbar", "self_available": "Version {} ist verfügbar (installiert: {}).\n\n{}",
        "self_release_notes": "Änderungen", "self_install": "Update installieren", "self_later": "Später",
        "self_downloading": "CraftUpdater {} wird heruntergeladen …", "self_installing": "Update wird installiert …",
        "self_installed_title": "Update installiert", "self_installed": "CraftUpdater {} wurde installiert. Jetzt neu starten?",
        "self_restart": "Jetzt neu starten", "self_restart_failed": "Das Update wurde installiert, aber CraftUpdater konnte nicht automatisch neu gestartet werden. Bitte starte es über das Anwendungsmenü.",
        "self_source_install": "Das Selbstupdate ist nur für die Debian-Paketinstallation verfügbar. Installiere CraftUpdater zuerst mit der bereitgestellten .deb-Datei.",
        "self_no_release": "Auf GitHub wurde noch kein veröffentlichtes CraftUpdater-Update gefunden.",
        "self_error": "CraftUpdater konnte nicht aktualisiert werden: {}",
    },
    "en": {
        "subtitle": "Manage your ArtCraft apps in one place", "version_label": "Version {}", "language": "Language",
        "check": "Check for updates", "installed": "Installed", "selected": "Selected",
        "sources": "Source available", "apps": "Your apps", "search": "Search",
        "updates": "Updates available", "app": "Application", "status": "Status",
        "installed_version": "Installed", "available_version": "Latest version", "commits": "Commits",
        "select_installed": "Select installed",
        "select_all": "Select all", "activity": "Activity", "clear": "Clear view",
        "ready": "Ready", "force": "Force rebuild", "update_selected": "Update selected",
        "none_title": "Nothing selected", "none_selected": "Select at least one app.",
        "check_run": "Checking for updates", "update_run": "App update", "running": "{} in progress …",
        "command_failed": "Command failed", "fetch": "Fetching changes …",
        "clone": "Cloning: {}", "building": "Building {} (this may take a few minutes) …",
        "binary_missing": "Built executable not found: {}",
        "already_current": "Already up to date; no rebuild needed.",
        "menu_installed": "Installed application menu entry: {}",
        "mime_installed": "Installed file type information ({} XML file(s)).",
        "no_desktop": "No matching menu entry found in the source; only the program was installed.",
        "install_path": "Installed: {}", "already_starts": "{}: starting update",
        "app_completed": "{}: complete", "checking_app": "{}: checking GitHub …",
        "waiting_clone": "Not cloned yet", "commits_waiting": "{} new commits", "up_to_date": "Up to date",
        "installed_status": "Installed · {}", "local": "Local", "system": "System",
        "source_status": "Source available", "missing_status": "Not installed",
        "failed": "Operation failed", "error_title": "Operation failed", "error_prefix": "ERROR:",
        "unknown_version": "Unknown", "no_version": "—", "cancel": "Cancel",
        "cancelling": "Cancelling …", "cancelled": "Cancelled", "close": "Close", "preflight": "Preflight checks",
        "preflight_ok": "Requirements met; {} GB free.",
        "missing_tools": "Required tools are missing: {}. Install Git, Rust/Cargo, pkg-config and nice.",
        "missing_package": "System library {} is missing. Install its development package.",
        "low_space": "Not enough free space: {} GB available, at least {} GB required.",
        "new_commits": "{} new commits", "version_check_failed": "Version check failed",
        "version_unknown": "Unknown",
        "update_complete_title": "Update complete",
        "update_complete_message": "The update operation has finished.\n\nProcessed: {}",
        "self_update": "Update CraftUpdater", "self_checking": "Checking for CraftUpdater updates …",
        "self_current_title": "CraftUpdater is up to date", "self_current": "You are already using CraftUpdater {}.",
        "self_available_title": "CraftUpdater update available", "self_available": "Version {} is available (installed: {}).\n\n{}",
        "self_release_notes": "Release notes", "self_install": "Install update", "self_later": "Later",
        "self_downloading": "Downloading CraftUpdater {} …", "self_installing": "Installing update …",
        "self_installed_title": "Update installed", "self_installed": "CraftUpdater {} was installed. Restart now?",
        "self_restart": "Restart now", "self_restart_failed": "The update was installed, but CraftUpdater could not restart automatically. Please launch it from the application menu.",
        "self_source_install": "Self-updates are available only for the Debian package installation. Install CraftUpdater from the provided .deb package first.",
        "self_no_release": "No published CraftUpdater update was found on GitHub yet.",
        "self_error": "CraftUpdater could not be updated: {}",
    },
}


@dataclass(frozen=True)
class Installation:
    kind: str
    location: str


def _message(translate, key: str, *args) -> str:
    template = translate(key) if translate else TEXTS["de"][key]
    return template.format(*args)


def _version_key(version: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", version)
    return tuple(int(number) for number in numbers) or (0,)


def _installed_deb_version() -> str | None:
    try:
        result = subprocess.run(
            ["dpkg-query", "-W", "-f=${Status}\n${Version}", "craft-updater"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    lines = result.stdout.splitlines()
    if result.returncode or len(lines) < 2 or lines[0] != "install ok installed":
        return None
    return lines[1].split(":")[-1]


class OperationCancelled(Exception):
    pass


def _check_cancel(cancel_event):
    if cancel_event and cancel_event.is_set():
        raise OperationCancelled()


def run(args: list[str], *, cwd: Path | None = None, on_line=None, translate=None,
        cancel_event=None, env: dict[str, str] | None = None) -> str:
    _check_cancel(cancel_event)
    proc = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1,
                            start_new_session=True, env=env)
    output = []
    assert proc.stdout is not None
    lines = queue.Queue()
    end = object()
    def collect():
        try:
            for line in proc.stdout:
                lines.put(line)
        finally:
            lines.put(end)
    reader = threading.Thread(target=collect, daemon=True)
    reader.start()
    ended = False
    while not ended:
        if cancel_event and cancel_event.is_set():
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            except ProcessLookupError:
                pass
            reader.join(timeout=1)
            raise OperationCancelled()
        try:
            line = lines.get(timeout=0.1)
        except queue.Empty:
            continue
        if line is end:
            ended = True
        else:
            output.append(line)
            if on_line:
                on_line(line.rstrip())
    code = proc.wait()
    if code:
        raise RuntimeError(f"{_message(translate, 'command_failed')} ({code}): {' '.join(args)}")
    return "".join(output)


def _normalized(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _app_id_matches(app_id: str, package: str) -> bool:
    return _normalized(app_id.rsplit(".", 1)[-1]) == _normalized(package)


@lru_cache(maxsize=1)
def _flatpak_app_ids() -> tuple[str, ...]:
    if not shutil.which("flatpak"):
        return ()
    try:
        result = subprocess.run(["flatpak", "list", "--app", "--columns=application"],
                                capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return ()
    return tuple(line.strip() for line in result.stdout.splitlines() if line.strip())


@lru_cache(maxsize=1)
def _snap_app_names() -> tuple[str, ...]:
    if not shutil.which("snap"):
        return ()
    try:
        result = subprocess.run(["snap", "list"], capture_output=True, text=True,
                                timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return ()
    return tuple(line.split()[0] for line in result.stdout.splitlines()[1:] if line.split())


def _from_command(tokens: list[str], package: str) -> Installation | None:
    if not tokens:
        return None
    command = tokens[0]
    command_name = Path(command).name
    if command_name in {"flatpak", "flatpak-spawn"}:
        for token in tokens[1:]:
            if _app_id_matches(token, package) and "." in token:
                return Installation("Flatpak", token)
    if command_name == "snap" and len(tokens) > 2 and tokens[1] == "run":
        if _normalized(Path(tokens[2]).name) == _normalized(package):
            return Installation("Snap", tokens[2])

    normalized_name = _normalized(command_name)
    if normalized_name == _normalized(package):
        resolved = shutil.which(command)
        candidate = Path(resolved or command).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return Installation("Programm", str(candidate.resolve()))
    if command_name.casefold().endswith(".appimage") and normalized_name.startswith(_normalized(package)):
        candidate = Path(command).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return Installation("AppImage", str(candidate.resolve()))
    return None


@lru_cache(maxsize=1)
def _known_portable_apps() -> tuple[Path, ...]:
    """Scan common AppImage folders and shallow /opt installs."""
    roots = (HOME / "Applications", HOME / "AppImages", HOME / "Downloads",
             HOME / "Desktop", HOME / "Schreibtisch", HOME / ".local" / "bin",
             Path("/usr/local/bin"), Path("/opt"))
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        if root == Path("/opt"):
            for current, dirs, files in os.walk(root):
                relative_depth = len(Path(current).relative_to(root).parts)
                dirs[:] = [name for name in dirs if not name.startswith(".") and relative_depth < 3]
                for name in files:
                    candidate = Path(current) / name
                    if name.casefold().endswith(".appimage") or _normalized(name) in {_normalized(app) for _, app in APPS}:
                        if os.access(candidate, os.X_OK):
                            found.append(candidate)
        else:
            found.extend(path for path in root.iterdir()
                         if path.is_file() and (path.name.casefold().endswith(".appimage")
                         or _normalized(path.name) in {_normalized(app) for _, app in APPS})
                         and os.access(path, os.X_OK))
    return tuple(found)


def installed_app(package: str) -> Installation | None:
    """Find native, Flatpak, Snap or AppImage installs for a Craft app."""
    managed = BIN_DIR / package
    if managed.is_file():
        return Installation("Benutzerinstallation", str(managed))
    found = shutil.which(package)
    if found:
        return Installation("Programm", str(Path(found).resolve()))

    for app_id in _flatpak_app_ids():
        if _app_id_matches(app_id, package):
            return Installation("Flatpak", app_id)
    for name in _snap_app_names():
        if _normalized(name) == _normalized(package):
            return Installation("Snap", name)
    for portable_app in _known_portable_apps():
        normalized_name = _normalized(portable_app.name)
        if normalized_name == _normalized(package) and not portable_app.name.casefold().endswith(".appimage"):
            return Installation("Programm", str(portable_app))
        if normalized_name.startswith(_normalized(package)) and portable_app.name.casefold().endswith(".appimage"):
            return Installation("AppImage", str(portable_app))

    for directory in DESKTOP_DIRS:
        if not directory.is_dir():
            continue
        for desktop in directory.glob("*.desktop"):
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(desktop, encoding="utf-8")
                entry = parser["Desktop Entry"]
                command = shlex.split(entry.get("Exec", ""))
            except (OSError, configparser.Error, ValueError):
                continue
            found = _from_command(command, package)
            if found:
                return found
            try:
                found = _from_command(shlex.split(entry.get("TryExec", "")), package)
            except ValueError:
                continue
            if found:
                return found
    return None


def install_desktop_integration(repo: Path, package: str, installed: Path, log, translate=None, cancel_event=None) -> None:
    """Install matching upstream launchers, icons and MIME declarations when present."""
    applications_dir = DATA_DIR / "applications"
    icons_dir = DATA_DIR / "icons" / "craft-updater" / package
    mime_dir = DATA_DIR / "mime" / "packages"
    desktop_files = []
    desktop_candidates = list(repo.rglob("*.desktop"))
    # Preserve the launcher's name, MIME associations and metadata from an
    # already installed system copy when this repository has no desktop file.
    for directory in DESKTOP_DIRS:
        if directory.is_dir():
            desktop_candidates.extend(directory.glob("*.desktop"))
    seen_desktops = set()
    for desktop in desktop_candidates:
        if "target" in desktop.parts or ".git" in desktop.parts:
            continue
        if desktop.name in seen_desktops:
            continue
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        try:
            parser.read(desktop, encoding="utf-8")
            entry = parser["Desktop Entry"]
        except (OSError, KeyError, configparser.Error):
            continue
        try:
            exec_parts = shlex.split(entry.get("Exec", ""))
            try_parts = shlex.split(entry.get("TryExec", ""))
        except ValueError:
            continue
        if not (_from_command(exec_parts, package) or _from_command(try_parts, package)):
            continue
        seen_desktops.add(desktop.name)
        desktop_files.append((desktop, parser, entry))

    if desktop_files:
        applications_dir.mkdir(parents=True, exist_ok=True)
    for source, parser, entry in desktop_files:
        exec_parts = shlex.split(entry.get("Exec", ""))
        if exec_parts:
            detected_command = _from_command(exec_parts, package)
            app_args = exec_parts[1:]
            if detected_command and detected_command.kind == "Flatpak":
                app_id_index = next((index for index, token in enumerate(exec_parts)
                                     if _app_id_matches(token, package) and "." in token), 0)
                app_args = exec_parts[app_id_index + 1:]
            elif detected_command and detected_command.kind == "Snap":
                app_args = exec_parts[3:]
            tokens = [str(installed), *app_args]
            # Desktop entry field codes (such as %U) must remain unquoted so
            # the file manager expands them to the selected file URI(s).
            entry["Exec"] = " ".join(
                token if token in {"%f", "%F", "%u", "%U", "%i", "%c", "%k"}
                else '"' + token.replace("\\", "\\\\").replace('"', '\\"') + '"'
                for token in tokens
            )
        try_exec = entry.get("TryExec", "")
        if try_exec:
            entry["TryExec"] = str(installed)
        icon_value = entry.get("Icon", "")
        if icon_value and not Path(icon_value).is_absolute():
            icon_source = next((p for p in repo.rglob("*")
                                if p.is_file() and p.suffix.lower() in {".png", ".svg", ".xpm"}
                                and p.stem.casefold() == Path(icon_value).stem.casefold()
                                and "target" not in p.parts and ".git" not in p.parts), None)
            if icon_source:
                icons_dir.mkdir(parents=True, exist_ok=True)
                icon_target = icons_dir / icon_source.name
                shutil.copy2(icon_source, icon_target)
                entry["Icon"] = str(icon_target)
        target = applications_dir / source.name
        with target.open("w", encoding="utf-8") as stream:
            parser.write(stream, space_around_delimiters=False)
        log(_message(translate, "menu_installed", target.name))

    mime_installed = 0
    for source in repo.rglob("*.xml"):
        if "target" in source.parts or ".git" in source.parts:
            continue
        try:
            root = ET.parse(source).getroot()
        except (OSError, ET.ParseError):
            continue
        if not any(element.tag.rsplit("}", 1)[-1] == "mime-type" for element in root.iter()):
            continue
        mime_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, mime_dir / f"craft-updater-{package}-{source.name}")
        mime_installed += 1
    if mime_installed and shutil.which("update-mime-database"):
        run(["update-mime-database", str(DATA_DIR / "mime")], on_line=log, translate=translate, cancel_event=cancel_event)
        log(_message(translate, "mime_installed", mime_installed))
    if not desktop_files:
        log(_message(translate, "no_desktop"))


def _preflight(repo: Path, package: str, log, translate, cancel_event):
    _check_cancel(cancel_event)
    required = ["git", "cargo", "rustc", "pkg-config", "nice"]
    missing = [name for name in required if not shutil.which(name)]
    if missing:
        raise RuntimeError(_message(translate, "missing_tools", ", ".join(missing)))
    libraries = ["gtk+-3.0"]
    if package in {"soundcraft", "filmcraft"}:
        libraries.append("alsa")
    for library in libraries:
        result = subprocess.run(["pkg-config", "--exists", library], check=False)
        if result.returncode:
            raise RuntimeError(_message(translate, "missing_package", library))
    disk = shutil.disk_usage(repo.parent if repo.parent.exists() else HOME)
    required_bytes = 3 * 1024**3 if repo.exists() else 5 * 1024**3
    if disk.free < required_bytes:
        raise RuntimeError(_message(translate, "low_space", round(disk.free / 1024**3, 1), round(required_bytes / 1024**3)))
    log(_message(translate, "preflight_ok", round(disk.free / 1024**3, 1)))


def update_app(repo_name: str, package: str, force: bool, log, translate=None, cancel_event=None) -> None:
    repo = REPOS / repo_name
    _preflight(repo, package, log, translate, cancel_event)
    REPOS.mkdir(parents=True, exist_ok=True)
    created_repo = not repo.exists()
    try:
        _check_cancel(cancel_event)
        if created_repo:
            log(_message(translate, "clone", f"https://github.com/storytold/{repo_name}.git"))
            run(["git", "clone", "https://github.com/storytold/" + repo_name + ".git", str(repo)], on_line=log, translate=translate, cancel_event=cancel_event)
        else:
            log(_message(translate, "fetch"))
            run(["git", "fetch", "origin"], cwd=repo, on_line=log, translate=translate, cancel_event=cancel_event)
            run(["git", "pull", "--ff-only"], cwd=repo, on_line=log, translate=translate, cancel_event=cancel_event)

        head = run(["git", "rev-parse", "HEAD"], cwd=repo, translate=translate, cancel_event=cancel_event).strip()
        if not force:
            try:
                old = (BUILD_STATE_DIR / f"{package}.commit").read_text().strip()
            except OSError:
                old = ""
            if old == head and (BIN_DIR / package).exists():
                install_desktop_integration(repo, package, BIN_DIR / package, log, translate, cancel_event)
                log(_message(translate, "already_current"))
                return

        _check_cancel(cancel_event)
        log(_message(translate, "building", package))
        build_env = os.environ.copy()
        build_env.setdefault("RUST_MIN_STACK", "16777216")
        run(["nice", "-n", "10", "cargo", "build", "--release", "--locked", "-p", package], cwd=repo, on_line=log, translate=translate, cancel_event=cancel_event, env=build_env)
        binary = repo / "target" / "release" / package
        if not binary.is_file():
            raise RuntimeError(_message(translate, "binary_missing", binary))
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        installed = BIN_DIR / package
        temporary = BIN_DIR / f".{package}.new"
        try:
            shutil.copy2(binary, temporary)
            temporary.chmod(temporary.stat().st_mode | 0o111)
            _check_cancel(cancel_event)
            os.replace(temporary, installed)
        finally:
            temporary.unlink(missing_ok=True)
        # Replacing the binary is the commit point. Finish metadata and record
        # the installed revision even if the user presses Cancel afterwards.
        install_desktop_integration(repo, package, installed, log, translate)
        BUILD_STATE_DIR.mkdir(parents=True, exist_ok=True)
        (BUILD_STATE_DIR / f"{package}.commit").write_text(head + "\n")
        log(_message(translate, "install_path", installed))
    except OperationCancelled:
        if created_repo and repo.exists():
            shutil.rmtree(repo, ignore_errors=True)
        raise


class CraftUpdater(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CraftUpdater")
        self.geometry("1200x740")
        self.minsize(1000, 640)
        self.events: queue.Queue = queue.Queue()
        self.busy = False
        self.cancel_event = None
        self.close_when_done = False
        self.latest_versions = {}
        self.commit_deltas = {}
        self.app_version = _installed_deb_version() or APP_VERSION
        self.language = self._load_language()
        self._configure_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._close_window)
        self._apply_language()
        self._refresh_status()
        installed_items = [item for item, (_, package) in self.items.items() if installed_app(package)]
        if installed_items:
            self.tree.selection_set(installed_items)
        self._update_selection_count()
        self.after(100, self._drain_events)

    def _load_language(self):
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8")).get("language", "de")
        except (OSError, ValueError, AttributeError):
            saved = "de"
        return saved if saved in TEXTS else "de"

    def _t(self, key):
        return TEXTS[self.language][key]

    def _set_language(self, _event=None):
        self.language = "en" if self.language_var.get() == "English" else "de"
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps({"language": self.language}, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass
        self._apply_language()
        self._refresh_status()

    def _apply_language(self):
        self.subtitle_label.configure(text=self._t("subtitle"))
        self.version_label.configure(text=self._t("version_label").format(self.app_version))
        self.language_label.configure(text=self._t("language"))
        self.check_btn.configure(text=self._t("check"))
        self.self_update_btn.configure(text=self._t("self_update"))
        self.stat_titles[0].configure(text=self._t("installed"))
        self.stat_titles[1].configure(text=self._t("selected"))
        self.stat_titles[2].configure(text=self._t("sources"))
        self.stat_titles[3].configure(text=self._t("updates"))
        self.apps_label.configure(text=self._t("apps"))
        self.search_label.configure(text=self._t("search"))
        self.tree.heading("#0", text=self._t("app"))
        self.tree.heading("status", text=self._t("status"))
        self.tree.heading("installed", text=self._t("installed_version"))
        self.tree.heading("available", text=self._t("available_version"))
        self.tree.heading("commits", text=self._t("commits"))
        self.select_installed_btn.configure(text=self._t("select_installed"))
        self.select_all_btn.configure(text=self._t("select_all"))
        self.activity_label.configure(text=self._t("activity"))
        self.clear_log_btn.configure(text=self._t("clear"))
        self.force_check.configure(text=self._t("force"))
        self.update_btn.configure(text=self._t("update_selected"))
        self.cancel_btn.configure(text=self._t("cancel"))
        self.close_btn.configure(text=self._t("close"))
        if not self.busy:
            self.status_var.set(self._t("ready"))

    def _configure_style(self):
        self.colors = {
            "background": "#f3f5f8", "surface": "#ffffff", "text": "#172033",
            "muted": "#68758b", "border": "#e2e7ef", "blue": "#315ee8",
            "blue_hover": "#244ac2", "green": "#21835b", "amber": "#a36612",
        }
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        self.configure(background=self.colors["background"])
        style.configure("TFrame", background=self.colors["background"])
        style.configure("Card.TFrame", background=self.colors["surface"], relief="solid",
                         borderwidth=1, bordercolor=self.colors["border"])
        style.configure("TLabel", background=self.colors["background"], foreground=self.colors["text"],
                         font=("TkDefaultFont", 10))
        style.configure("Title.TLabel", font=("TkDefaultFont", 24, "bold"), foreground=self.colors["text"])
        style.configure("Subtitle.TLabel", font=("TkDefaultFont", 10), foreground=self.colors["muted"])
        style.configure("Section.TLabel", background=self.colors["surface"], font=("TkDefaultFont", 12, "bold"), foreground=self.colors["text"])
        style.configure("CardLabel.TLabel", background=self.colors["surface"], font=("TkDefaultFont", 9), foreground=self.colors["muted"])
        style.configure("CardValue.TLabel", background=self.colors["surface"], font=("TkDefaultFont", 20, "bold"), foreground=self.colors["text"])
        style.configure("TButton", padding=(13, 9), font=("TkDefaultFont", 10))
        style.configure("Primary.TButton", background=self.colors["blue"], foreground="#ffffff",
                         borderwidth=0, padding=(16, 10), font=("TkDefaultFont", 10, "bold"))
        style.map("Primary.TButton", background=[("disabled", "#aab8ed"), ("active", self.colors["blue_hover"])],
                  foreground=[("disabled", "#f7f8fc"), ("!disabled", "#ffffff")])
        style.configure("Treeview", background=self.colors["surface"], fieldbackground=self.colors["surface"],
                         foreground=self.colors["text"], rowheight=34, borderwidth=0,
                         font=("TkDefaultFont", 10))
        style.map("Treeview", background=[("selected", "#dce6ff")],
                  foreground=[("selected", self.colors["text"])])
        style.configure("Treeview.Heading", background="#f7f8fb", foreground=self.colors["muted"],
                         font=("TkDefaultFont", 9, "bold"), padding=(8, 9), relief="flat")
        style.configure("TEntry", padding=(9, 8), fieldbackground=self.colors["surface"])
        style.configure("TCheckbutton", background=self.colors["surface"], foreground=self.colors["muted"])
        style.configure("Horizontal.TProgressbar", troughcolor="#e6ebf4", background=self.colors["blue"],
                         borderwidth=0, thickness=8)

    def _build_ui(self):
        root = ttk.Frame(self, padding=(26, 22, 26, 20))
        root.pack(fill="both", expand=True)
        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 18))
        title_area = ttk.Frame(header)
        title_area.pack(side="left", fill="x", expand=True)
        ttk.Label(title_area, text="CraftUpdater", style="Title.TLabel").pack(anchor="w")
        self.subtitle_label = ttk.Label(title_area, text="", style="Subtitle.TLabel")
        self.subtitle_label.pack(anchor="w", pady=(3, 0))
        self.version_label = ttk.Label(title_area, text="", style="Subtitle.TLabel")
        self.version_label.pack(anchor="w", pady=(2, 0))
        language_area = ttk.Frame(header)
        language_area.pack(side="right", padx=(12, 0))
        self.language_label = ttk.Label(language_area, text="", style="Subtitle.TLabel")
        self.language_label.pack(side="left", padx=(0, 6))
        self.language_var = tk.StringVar(value="English" if self.language == "en" else "Deutsch")
        self.language_combo = ttk.Combobox(language_area, textvariable=self.language_var,
                                           values=("Deutsch", "English"), state="readonly", width=10)
        self.language_combo.pack(side="left")
        self.language_combo.bind("<<ComboboxSelected>>", self._set_language)
        self.check_btn = ttk.Button(header, text="Updates prüfen", command=self._check_updates)
        self.check_btn.pack(side="right", anchor="center")
        self.self_update_btn = ttk.Button(header, text="", command=self._check_self_update)
        self.self_update_btn.pack(side="right", anchor="center", padx=(0, 8))

        stats = ttk.Frame(root)
        stats.pack(fill="x", pady=(0, 18))
        self.installed_count = tk.StringVar(value="0")
        self.selection_count = tk.StringVar(value="0")
        self.source_count = tk.StringVar(value="0")
        self.updates_count = tk.StringVar(value="0")
        self.stat_titles = []
        self._stat_card(stats, "", self.installed_count).pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._stat_card(stats, "", self.selection_count).pack(side="left", fill="x", expand=True, padx=5)
        self._stat_card(stats, "", self.source_count).pack(side="left", fill="x", expand=True, padx=(10, 0))
        self._stat_card(stats, "", self.updates_count).pack(side="left", fill="x", expand=True, padx=(10, 0))

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        app_card = ttk.Frame(body, style="Card.TFrame", padding=16)
        app_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        log_card = ttk.Frame(body, style="Card.TFrame", padding=16)
        log_card.pack(side="left", fill="both", expand=True, padx=(10, 0))

        app_header = ttk.Frame(app_card, style="Card.TFrame")
        app_header.pack(fill="x", pady=(0, 12))
        self.apps_label = ttk.Label(app_header, text="", style="Section.TLabel")
        self.apps_label.pack(side="left")
        self.force_var = tk.BooleanVar(value=False)
        self.force_check = ttk.Checkbutton(app_header, text="", variable=self.force_var)
        self.force_check.pack(side="left", padx=(14, 0))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self._filter_apps)
        self.filter_entry = ttk.Entry(app_header, textvariable=self.filter_var, width=22)
        self.filter_entry.pack(side="right")
        self.search_label = ttk.Label(app_header, text="", style="CardLabel.TLabel")
        self.search_label.pack(side="right", padx=(0, 8))

        app_controls = ttk.Frame(app_card, style="Card.TFrame")
        app_controls.pack(fill="x", pady=(0, 12))
        self.select_installed_btn = ttk.Button(app_controls, text="", command=self._select_installed)
        self.select_installed_btn.pack(side="left")
        self.update_btn = ttk.Button(app_controls, text="", style="Primary.TButton", command=self._update_selected)
        self.update_btn.pack(side="left", padx=8)
        self.select_all_btn = ttk.Button(app_controls, text="", command=self._select_all)
        self.select_all_btn.pack(side="right")

        tree_frame = ttk.Frame(app_card, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=("status", "installed", "available", "commits"), show="tree headings", selectmode="extended")
        self.tree.heading("#0", text="Anwendung", anchor="w")
        self.tree.heading("status", text="Status", anchor="w")
        self.tree.column("#0", width=150, minwidth=125, stretch=True)
        self.tree.column("status", width=185, minwidth=145, stretch=True)
        for column, width in (("installed", 92), ("available", 105), ("commits", 65)):
            self.tree.column(column, width=width, minwidth=65, stretch=False, anchor="center")
        self.tree.tag_configure("installed", foreground=self.colors["green"])
        self.tree.tag_configure("source", foreground=self.colors["amber"])
        self.tree.tag_configure("missing", foreground=self.colors["muted"])
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._update_selection_count())
        self.items = {}
        for name, package in APPS:
            item = self.tree.insert("", "end", text=name, values=("Prüfe …", "—", "—", "—"))
            self.items[item] = (name, package)

        log_header = ttk.Frame(log_card, style="Card.TFrame")
        log_header.pack(fill="x", pady=(0, 12))
        self.activity_label = ttk.Label(log_header, text="", style="Section.TLabel")
        self.activity_label.pack(side="left")
        self.clear_log_btn = ttk.Button(log_header, text="", command=self._clear_log)
        self.clear_log_btn.pack(side="right")
        self.cancel_btn = ttk.Button(log_header, text="", command=self._cancel_operation, state="disabled")
        self.cancel_btn.pack(side="right", padx=(0, 8))
        self.close_btn = ttk.Button(log_header, text="", command=self._close_window)
        self.close_btn.pack(side="right", padx=(0, 8))
        self.log = tk.Text(log_card, wrap="word", state="disabled", height=18,
                           background="#172033", foreground="#dbe4f3", insertbackground="#ffffff",
                           relief="flat", borderwidth=0, padx=12, pady=12,
                           font=("TkFixedFont", 9), selectbackground="#315ee8")
        scroll = ttk.Scrollbar(log_card, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        footer = ttk.Frame(root)
        footer.pack(fill="x", pady=(16, 0))
        self.status_var = tk.StringVar(value="Bereit")
        ttk.Label(footer, textvariable=self.status_var, style="Subtitle.TLabel").pack(side="left")
        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=130)
        self.progress.pack(side="right", padx=(12, 0))

    def _stat_card(self, parent, title, value):
        card = ttk.Frame(parent, style="Card.TFrame", padding=(16, 12))
        title_label = ttk.Label(card, text=title, style="CardLabel.TLabel")
        title_label.pack(anchor="w")
        self.stat_titles.append(title_label)
        ttk.Label(card, textvariable=value, style="CardValue.TLabel").pack(anchor="w", pady=(3, 0))
        return card

    def _filter_apps(self, *_args):
        query = self.filter_var.get().strip().casefold()
        for item, (name, _package) in self.items.items():
            if query in name.casefold():
                if self.tree.parent(item) == "" and item not in self.tree.get_children():
                    self.tree.reattach(item, "", "end")
            elif item in self.tree.get_children():
                self.tree.detach(item)

    def _select_all(self):
        self.tree.selection_set(self.tree.get_children())

    def _select_installed(self):
        matches = [item for item, (_name, package) in self.items.items() if installed_app(package)]
        self.tree.selection_set([item for item in matches if item in self.tree.get_children()])

    def _update_selection_count(self):
        self.selection_count.set(str(len(self.tree.selection())))

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _append(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as stream:
            stream.write(text + "\n")

    def _refresh_status(self):
        installed = 0
        sources = 0
        for item, (name, package) in self.items.items():
            repo = REPOS / name
            detected = installed_app(package)
            if detected:
                installed += 1
                kind = {"Benutzerinstallation": self._t("local"), "Programm": self._t("system")}.get(detected.kind, detected.kind)
                status = self._t("installed_status").format(kind)
                tag = "installed"
            elif repo.exists():
                status = self._t("source_status")
                sources += 1
                tag = "source"
            else:
                status = self._t("missing_status")
                tag = "missing"
            self.tree.set(item, "status", status)
            marker = BUILD_STATE_DIR / f"{package}.commit"
            try:
                installed_version = marker.read_text(encoding="utf-8").strip()[:8]
            except OSError:
                installed_version = self._t("unknown_version") if detected else self._t("no_version")
            latest = self.latest_versions.get(package)
            self.tree.set(item, "installed", installed_version)
            self.tree.set(item, "available", latest[:8] if latest else self._t("no_version"))
            delta = self.commit_deltas.get(package)
            self.tree.set(item, "commits", str(delta) if delta is not None else self._t("no_version"))
            self.tree.item(item, tags=(tag,))
        self.installed_count.set(str(installed))
        self.source_count.set(str(sources))
        self.updates_count.set(str(sum(1 for count in self.commit_deltas.values() if count and count > 0)))
        self._update_selection_count()

    def _selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(self._t("none_title"), self._t("none_selected"))
            return []
        return [self.items[item] for item in selected]

    def _start(self, title, operation, *, cancellable=True):
        if self.busy:
            return
        self.busy = True
        self.cancel_event = threading.Event()
        self.operation_cancellable = cancellable
        self.check_btn.configure(state="disabled")
        self.self_update_btn.configure(state="disabled")
        self.update_btn.configure(state="disabled")
        self.language_combo.configure(state="disabled")
        self.cancel_btn.configure(state="normal" if cancellable else "disabled")
        if not cancellable:
            self.close_btn.configure(state="disabled")
        self.status_var.set(self._t("running").format(title))
        self.progress.start(12)
        self._append(f"\n── {title} ──")
        def worker():
            try:
                completed = operation()
                if completed is not False:
                    self.events.put(("done", None))
            except OperationCancelled:
                self.events.put(("cancelled", None))
            except Exception as exc:
                self.events.put(("error", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def _cancel_operation(self):
        if self.cancel_event and self.busy and self.operation_cancellable:
            self.cancel_event.set()
            self.cancel_btn.configure(state="disabled")
            self.status_var.set(self._t("cancelling"))

    def _close_window(self):
        if self.busy:
            if not self.operation_cancellable:
                return
            self.close_when_done = True
            if self.cancel_event:
                self.cancel_event.set()
                self.cancel_btn.configure(state="disabled")
                self.status_var.set(self._t("cancelling"))
            return
        self.destroy()

    def _check_updates(self):
        translate = lambda key: TEXTS[self.language][key]
        def operation():
            for item, (name, package) in self.items.items():
                _check_cancel(self.cancel_event)
                repo = REPOS / name
                self.events.put(("log", self._t("checking_app").format(name)))
                if repo.exists():
                    run(["git", "fetch", "origin"], cwd=repo,
                        on_line=lambda line: self.events.put(("log", line)), translate=translate, cancel_event=self.cancel_event)
                    remote = run(["git", "rev-parse", "@{u}"], cwd=repo, translate=translate, cancel_event=self.cancel_event).strip()
                    try:
                        base = (BUILD_STATE_DIR / f"{package}.commit").read_text().strip()
                    except OSError:
                        base = run(["git", "rev-parse", "HEAD"], cwd=repo, translate=translate, cancel_event=self.cancel_event).strip()
                    count = int(run(["git", "rev-list", f"{base}..{remote}", "--count"], cwd=repo, translate=translate, cancel_event=self.cancel_event).strip())
                else:
                    output = run(["git", "ls-remote", "https://github.com/storytold/" + name + ".git", "HEAD"], translate=translate, cancel_event=self.cancel_event).strip()
                    remote = output.split()[0] if output else ""
                    try:
                        base = (BUILD_STATE_DIR / f"{package}.commit").read_text().strip()
                    except OSError:
                        base = ""
                    count = 0 if base and base == remote else None
                self.events.put(("version", (package, remote, count)))
                status = self._t("commits_waiting").format(count) if count else self._t("up_to_date") if count == 0 else self._t("version_unknown")
                self.events.put(("status", (item, "status", status)))
        self._start(self._t("check_run"), operation)

    def _update_selected(self):
        selected = self._selected()
        if not selected:
            return
        force = self.force_var.get()
        translate = lambda key: TEXTS[self.language][key]
        def operation():
            for name, package in selected:
                self.events.put(("log", "\n" + self._t("already_starts").format(name)))
                _check_cancel(self.cancel_event)
                update_app(name, package, force, lambda line: self.events.put(("log", line)), translate, self.cancel_event)
                self.events.put(("log", self._t("app_completed").format(name)))
            self.events.put(("refresh", None))
            self.events.put(("update_complete", ", ".join(name for name, _package in selected)))
        self._start(self._t("update_run"), operation)

    def _check_self_update(self):
        translate = lambda key: TEXTS[self.language][key]
        self.self_update_btn.configure(state="disabled")
        self.status_var.set(self._t("self_checking"))

        def operation():
            installed = _installed_deb_version()
            if not installed:
                self.events.put(("self_update_source", None))
                return
            request = urllib.request.Request(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                headers={"Accept": "application/vnd.github+json", "User-Agent": "CraftUpdater"},
            )
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    release = json.loads(response.read(2_000_000).decode("utf-8"))
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    self.events.put(("self_update_none", None))
                    return
                raise RuntimeError(f"GitHub API: HTTP {error.code}") from error
            tag = str(release.get("tag_name", "")).strip()
            version = tag.removeprefix("v").removeprefix("V")
            if not version:
                raise RuntimeError("GitHub release has no version tag")
            if _version_key(version) <= _version_key(installed):
                self.events.put(("self_update_current", installed))
                return
            asset_name = f"craft-updater_{version}_all.deb"
            asset = next((item for item in release.get("assets", [])
                          if item.get("name") == asset_name), None)
            if not asset or not str(asset.get("browser_download_url", "")).startswith("https://"):
                raise RuntimeError(f"Release asset {asset_name} is missing")
            self.events.put(("self_update_available", {
                "version": version, "installed": installed,
                "notes": str(release.get("body", "")).strip(),
                "url": asset["browser_download_url"], "name": asset_name,
            }))

        self._start(self._t("self_checking"), operation)

    def _install_self_update(self, release):
        self.self_update_btn.configure(state="disabled")
        self.status_var.set(self._t("self_downloading").format(release["version"]))

        def operation():
            cache_dir = Path.home() / ".cache" / "craft-updater" / "updates"
            cache_dir.mkdir(parents=True, exist_ok=True)
            package = cache_dir / release["name"]
            request = urllib.request.Request(
                release["url"], headers={"User-Agent": "CraftUpdater"},
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response, package.open("wb") as output:
                    shutil.copyfileobj(response, output)
                if package.stat().st_size < 1024:
                    raise RuntimeError("Downloaded Debian package is unexpectedly small")
                self.events.put(("self_update_installing", None))
                result = subprocess.run(
                    ["pkexec", "apt-get", "install", "-y", str(package)],
                    capture_output=True, text=True, timeout=900, check=False,
                )
                if result.returncode:
                    detail = (result.stderr or result.stdout).strip().splitlines()
                    raise RuntimeError(detail[-1] if detail else f"Installer exited with code {result.returncode}")
                self.events.put(("self_update_installed", release["version"]))
                return False
            except Exception:
                package.unlink(missing_ok=True)
                raise

        self._start(self._t("self_installing"), operation, cancellable=False)

    def _restart_after_self_update(self):
        executable = Path("/usr/bin/craft-updater")
        try:
            subprocess.Popen([str(executable)], start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            messagebox.showinfo(self._t("self_installed_title"), self._t("self_restart_failed"))
        self.destroy()

    def _drain_events(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log": self._append(value)
                elif kind == "status": self.tree.set(*value)
                elif kind == "refresh": self._refresh_status()
                elif kind == "version":
                    package, latest, count = value
                    self.latest_versions[package] = latest
                    self.commit_deltas[package] = count
                    self._refresh_status()
                elif kind == "cancelled":
                    self._finish_operation(self._t("cancelled"))
                elif kind == "update_complete":
                    messagebox.showinfo(
                        self._t("update_complete_title"),
                        self._t("update_complete_message").format(value),
                    )
                elif kind == "self_update_source":
                    self.self_update_btn.configure(state="normal")
                    self._finish_operation(self._t("ready"))
                    messagebox.showinfo(self._t("self_update"), self._t("self_source_install"))
                elif kind == "self_update_none":
                    self.self_update_btn.configure(state="normal")
                    self._finish_operation(self._t("ready"))
                    messagebox.showinfo(self._t("self_update"), self._t("self_no_release"))
                elif kind == "self_update_current":
                    self.self_update_btn.configure(state="normal")
                    self._finish_operation(self._t("ready"))
                    messagebox.showinfo(self._t("self_current_title"), self._t("self_current").format(value))
                elif kind == "self_update_available":
                    self.self_update_btn.configure(state="normal")
                    self._finish_operation(self._t("ready"))
                    self._show_self_update_dialog(value)
                elif kind == "self_update_installing":
                    self.status_var.set(self._t("self_installing"))
                elif kind == "self_update_installed":
                    self._finish_operation(self._t("ready"))
                    if messagebox.askyesno(
                        self._t("self_installed_title"),
                        self._t("self_installed").format(value),
                        detail=self._t("self_restart"),
                    ):
                        self._restart_after_self_update()
                    else:
                        self.self_update_btn.configure(state="normal")
                elif kind == "error":
                    self._append(self._t("error_prefix") + " " + value)
                    self._refresh_status()
                    self._finish_operation(self._t("failed"))
                    messagebox.showerror(self._t("error_title"), value)
                elif kind == "done":
                    self._finish_operation(self._t("ready"))
                    self._refresh_status()
        except queue.Empty:
            pass
        if self.close_when_done and not self.busy:
            self.destroy()
            return
        self.after(100, self._drain_events)

    def _finish_operation(self, status):
        self.busy = False
        self.cancel_event = None
        self.operation_cancellable = True
        self.check_btn.configure(state="normal")
        self.self_update_btn.configure(state="normal")
        self.update_btn.configure(state="normal")
        self.language_combo.configure(state="readonly")
        self.cancel_btn.configure(state="disabled")
        self.close_btn.configure(state="normal")
        self.progress.stop()
        self.status_var.set(status)

    def _show_self_update_dialog(self, release):
        dialog = tk.Toplevel(self)
        dialog.title(self._t("self_available_title"))
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        dialog.geometry("560x390")
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=self._t("self_available").format(
            release["version"], release["installed"], ""
        ).rstrip(), style="Section.TLabel").pack(anchor="w", pady=(0, 12))
        ttk.Label(frame, text=self._t("self_release_notes"), style="Section.TLabel").pack(anchor="w")
        notes = tk.Text(frame, wrap="word", height=12, state="normal", padx=10, pady=8)
        notes.pack(fill="both", expand=True, pady=(6, 14))
        notes.insert("1.0", release["notes"] or self._t("self_no_release"))
        notes.configure(state="disabled")
        actions = ttk.Frame(frame)
        actions.pack(fill="x")
        ttk.Button(actions, text=self._t("self_later"), command=dialog.destroy).pack(side="right")
        ttk.Button(actions, text=self._t("self_install"), style="Primary.TButton",
                   command=lambda: (dialog.destroy(), self._install_self_update(release))).pack(side="right", padx=(0, 8))


if __name__ == "__main__":
    CraftUpdater().mainloop()
