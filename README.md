# CraftUpdater

A lightweight Linux desktop app for checking and updating the open source ArtCraft applications from GitHub releases.

## Screenshots

**Application list, installation status, and activity log**

![CraftUpdater main window](assets/img/main-window.png)

**Installing a CraftUpdater update**

![CraftUpdater update dialog with release notes](assets/img/updater_CraftUpdater.png)

**Checking for updates and viewing activity**

![CraftUpdater building an update](assets/img/main-window-2.png)

**Completion message**

![CraftUpdater update complete message](assets/img/update_finished.png)

## Features

- Check GitHub Releases for the latest version of each supported app.
- See installed and available release versions and whether an update is available.
- Detect common existing installations, including native programs, Flatpak, Snap, and AppImages.
- Rescan every supported app and show the detected installation type and path in the activity log. Apps without a detected installation are reported as not installed.
- Download the matching Linux `.deb` package for the system architecture and install it through the system package manager.
- Verify the package checksum and identity before installation.
- Cancel a running download or installation. Package installation uses the system authentication prompt.
- Get a completion dialog listing the apps processed after a successful update operation.
- Switch the interface between German and English.
- Check GitHub Releases for CraftUpdater updates, review release notes, and install the new Debian package from the GUI with an administrator authentication prompt.
- View download and installation output in the app and in a persistent log file.
- Resize table columns by dragging their dividers, or double-click a divider to fit the column to its heading and visible values. Resize the table and activity log areas by dragging their divider.
- Open PDFs with PdfCraft from the file manager using **Open With**. The installed desktop entry passes selected PDF paths correctly; CraftUpdater keeps the `%U` file argument unquoted so the desktop environment can expand it.

## Supported applications

PdfCraft, WordCraft, GridCraft, DeckCraft, PhotoCraft, LightCraft, VectorCraft, DesignCraft, CADCraft, SoundCraft, FilmCraft, and EffectCraft.

## Requirements

- Linux, Python 3, and Tkinter
- `dpkg`, `apt-get`, and `pkexec` (normally available on Debian and Ubuntu)
- An internet connection

On Debian or Ubuntu, install the common prerequisites with:

```sh
sudo apt install python3 python3-tk pkexec
```

## Run

Clone this repository, then start the GUI:

```sh
git clone https://github.com/wildcardcharacter/CraftUpdater-ArtCraft-App-Updater-for-Linux.git
cd CraftUpdater-ArtCraft-App-Updater-for-Linux
./craft_updater.py
```

To add CraftUpdater to your application menu and install a command in `~/.local/bin`:

```sh
./install.sh
```

## Debian package

Build a Debian package with the application menu entry and scalable icon:

```sh
./build-deb.sh
```

The package is created at `dist/craft-updater_0.3.0_all.deb`. Install it with:

```sh
sudo apt install ./dist/craft-updater_0.3.0_all.deb
```

You can pass a package version to the build script, for example `./build-deb.sh 0.3.0`.

### Updating CraftUpdater

Use **Update CraftUpdater** in the window header to check the latest GitHub release. When a newer version is available, CraftUpdater displays its release notes. Choosing **Install update** downloads the matching `.deb` asset and opens the system authentication prompt to install it. The installer closes after installation and offers to start the updated version. This self-update is available when CraftUpdater was installed from a Debian package; source installations should be updated by downloading or building the newer package manually.

Click **Check app updates** to query each app's latest GitHub Release. Select apps in the table, then click **Update selected apps**. The latest `.deb` for the computer's x86_64 or ARM64 architecture is downloaded, checked against the release SHA-256, and installed with `apt-get` after administrator authentication. If a matching package or checksum is unavailable, that app's update is stopped with an error. A prior CraftUpdater-managed binary in `~/.local/bin` is removed after the package installs successfully so it cannot shadow the system package.

## How updates work

The `.deb` packages are installed system-wide by `apt-get`; dependencies declared by the upstream package are handled by the package manager. Existing user settings and documents are not changed. Apps that were previously installed by CraftUpdater from source are migrated when their package is installed: the old user-local executable and its generated launcher override are removed after a successful installation.

The language preference is saved in `~/.config/craft-updater-gui/settings.json`. The activity log is saved in `~/.local/state/craft-updater-gui/last-run.log`.

## License and affiliation

CraftUpdater is an independent, unofficial community project and is not affiliated with or endorsed by ArtCraft. See the repository license for the terms that apply to this project.
