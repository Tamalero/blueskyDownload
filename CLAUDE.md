# BlueSkyDownload — Claude Context

## Project at a glance

Personal Python tool to download media (images + videos) from Bluesky using the AT Protocol REST API.
Two entry points: a CLI (`apitest.py`) and a PyQt6 GUI (`gui.py`).

- **GitHub:** https://github.com/Tamalero/blueskyDownload  
- **Platform:** Arch/CachyOS, x86_64  
- **Python:** system Python 3 (no virtualenv — all deps via pacman)  
- **XDG config:** `~/.config/blueskydownload/config.ini`  
- **Default output:** `~/Pictures/BlueSkyDownload`
- **Latest release:** v1.3.0 — https://github.com/Tamalero/blueskyDownload/releases/tag/v1.3.0

---

## Repository state (as of 2026-05-05)

Git is initialized. Remote is `https://github.com/Tamalero/blueskyDownload.git`, branch `main`.
Latest commit: `f634126` — "Add self-contained Linux AppImage CI build job"

Committed files:

```
.github/workflows/build-windows.yml  ← CI: builds BlueSkyDownloader.exe on Windows runner
.gitignore
CLAUDE.md
README.md
apitest.py            ← main CLI + shared library
blueskydownload.png   ← app icon (256×256), committed here for CI access
blueskydownload.desktop
gui.py                ← PyQt6 GUI (imports apitest)
imagedownload.sh
requirements.txt
```

**Not committed** (covered by `.gitignore`): `config.ini`, `credentials.txt`, `data.json`,
`backup.tar.gz`, `urls.txt`, `url_list.txt`, `downloaded_images/`, `Downloads/`, `*.AppImage`,
`*.AppDir/`, `__pycache__/`

Obsolete files still on disk (not tracked by git): `apitest_backup.py`, `apitest_backup2.py`,
`downloadlikes.py`, `singledownload.py`, `generic.py`, `newversion.py`, `newcookies.py`,
`logintest.py`, `test.py`, `startenv.sh`.

---

## System dependencies (all installed via pacman)

| Package | Status |
|---|---|
| `python-requests` | installed |
| `python-tqdm` | installed |
| `python-pyqt6` | installed |
| `python-cryptography` | installed |
| `yt-dlp` | installed |
| `ffmpeg` | installed |
| `appimagetool-bin` | installed (AUR) |
| `zsyncmake` | installed (bundled with zsync package) |

---

## AppImage

Type 2 AppImage with embedded GitHub update metadata:

```
BlueSkyDownloader-x86_64.AppImage       (squashfs/zstd, ELF runtime)
BlueSkyDownloader-x86_64.AppImage.zsync (delta-update index)
```

Both files are attached to GitHub releases and built by CI (`build-linux` job). Not committed to git.

### Distributable AppImage (CI-built, self-contained)

The release AppImage is built by GitHub Actions on `ubuntu-latest` using PyInstaller `--onefile`.
It bundles Python, all packages (PyQt6, yt-dlp, cryptography, requests, tqdm), and static
ffmpeg/ffprobe binaries. No system Python or pacman packages required on the end user's machine.

AppDir structure assembled in CI:
```
AppDir/
├── AppRun                  (bash: exec "$APPDIR/BlueSkyDownloader" "$@")
├── blueskydownload.desktop
├── blueskydownload.png
└── BlueSkyDownloader       (PyInstaller --onefile binary)
```

The zsync file is generated automatically by appimagetool when `-u` is provided.

### Local AppDir (thin, for development only)

`BlueSkyDownloader.AppDir/` on disk is a thin dev wrapper — it runs the Python scripts directly
using system Python/pacman packages. Use it only for local testing on Arch/CachyOS.

```
BlueSkyDownloader.AppDir/
├── AppRun                  (bash launcher → python3 usr/bin/gui.py)
├── blueskydownload.desktop
├── blueskydownload.png
└── usr/bin/
    ├── apitest.py
    └── gui.py
```

Local thin rebuild (dev only):
```bash
cp apitest.py gui.py BlueSkyDownloader.AppDir/usr/bin/
rm -f BlueSkyDownloader-x86_64.AppImage
ARCH=x86_64 appimagetool \
  -u "gh-releases-zsync|Tamalero|blueskyDownload|latest|BlueSkyDownloader-x86_64.AppImage.zsync" \
  BlueSkyDownloader.AppDir BlueSkyDownloader-x86_64.AppImage
```

### Auto-update (end-user)

```bash
AppImageUpdate BlueSkyDownloader-x86_64.AppImage
```

Requires [AppImageUpdate](https://github.com/AppImageCommunity/AppImageUpdate) to be installed.
The AppImage's embedded update URL resolves to the latest release on GitHub.

---

## CI builds

The workflow file is `.github/workflows/build-windows.yml` (renamed to "Build Releases" in title).
Both jobs run in parallel on every published release or `workflow_dispatch`.

### Triggers

| Event | Behaviour |
|---|---|
| New release published | Both jobs build and attach assets automatically |
| `workflow_dispatch` | Manual trigger; requires `tag_name` input (e.g. `v1.3.0`) |

Manual trigger command:
```bash
gh workflow run "Build Releases" --repo Tamalero/blueskyDownload --ref main -f tag_name=vX.Y.Z
```

### Windows build (`build-windows` job, `windows-latest`)

1. Installs Python 3.12 + `pyinstaller pyqt6 requests tqdm pillow cryptography yt-dlp`
2. Downloads `ffmpeg.exe` + `ffprobe.exe` from BtbN static builds (latest win64-gpl)
3. Converts `blueskydownload.png` → `blueskydownload.ico` (multi-res: 16/32/48/256 px) via Pillow
4. Runs PyInstaller `--onefile --windowed --collect-all PyQt6 --collect-all yt_dlp --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;."`
5. Uploads `dist/BlueSkyDownloader.exe` to the release

### Linux AppImage build (`build-linux` job, `ubuntu-latest`)

1. Installs Python 3.12 + system Qt libs + `pyinstaller pyqt6 requests tqdm cryptography yt-dlp`
2. Downloads `ffmpeg` + `ffprobe` from BtbN static builds (latest linux64-gpl)
3. Runs PyInstaller `--onefile --windowed --collect-all PyQt6 --collect-all yt_dlp --add-binary "ffmpeg:." --add-binary "ffprobe:."`
4. Assembles a minimal AppDir with the binary, icon, desktop file, and AppRun launcher script
5. Downloads `appimagetool` and runs it with `--appimage-extract-and-run` and `-u` (auto-generates zsync)
6. Uploads `BlueSkyDownloader-x86_64.AppImage` + `.zsync` to the release

### PyInstaller flags (both platforms)

| Flag | Reason |
|---|---|
| `--onefile` | Single portable binary — no install needed |
| `--windowed` | No console window on launch |
| `--collect-all PyQt6` | Bundles all Qt plugins (Windows: `qwindows.dll`; Linux: `xcb`, `wayland`) |
| `--collect-all yt_dlp` | Bundles all yt-dlp extractor/downloader modules (uses dynamic imports) |
| `--add-binary "ffmpeg[.exe]:."` | Static ffmpeg in bundle root (`sys._MEIPASS`) |
| `--add-binary "ffprobe[.exe]:."` | Static ffprobe in bundle root |

`--onefile` extracts to a persistent temp folder on first launch; subsequent launches reuse it.
`_download_video` detects `sys.frozen` and sets `yt_dlp`'s `ffmpeg_location` to `sys._MEIPASS`.

### yt-dlp integration

`_download_video` uses the `yt_dlp` Python API (no subprocess). On Linux (local/AppImage local dev),
`yt-dlp` must be installed via pacman. In the distributable AppImage and Windows exe, it is bundled.

---

## GitHub releases

| Tag | Assets |
|---|---|
| `v1.3.0` | `BlueSkyDownloader.exe`, `BlueSkyDownloader-x86_64.AppImage`, `BlueSkyDownloader-x86_64.AppImage.zsync`, source zip/tar.gz |
| `v1.2.0` | `BlueSkyDownloader.exe`, `BlueSkyDownloader-x86_64.AppImage`, `BlueSkyDownloader-x86_64.AppImage.zsync`, source zip/tar.gz |
| `v1.1.0` | `BlueSkyDownloader.exe`, `BlueSkyDownloader-x86_64.AppImage`, `BlueSkyDownloader-x86_64.AppImage.zsync`, source zip/tar.gz |
| `v1.0.0` | `BlueSkyDownloader-x86_64.AppImage`, `BlueSkyDownloader-x86_64.AppImage.zsync`, source zip/tar.gz |

When making a new release:
1. Commit and push code changes to `main`
2. `gh release create vX.Y.Z --title "..." --notes "..."`
3. GitHub Actions builds **both** the Windows exe and the self-contained Linux AppImage (+ zsync) automatically and attaches them within ~10 minutes

No local AppImage rebuild needed for releases — CI handles everything.

The source code zip/tar.gz is auto-attached by GitHub for every release.

---

## Desktop launcher

`blueskydownload.desktop` is in the project root and committed to git.
It is **not yet installed** to `~/.local/share/applications/` (user declined).

To install:
```bash
cp blueskydownload.desktop ~/.local/share/applications/
# Edit Exec= to the absolute path of gui.py
```

---

## Running

```bash
# GUI
python gui.py

# CLI — liked posts
python apitest.py --mode likes

# CLI — any user's gallery
python apitest.py --mode gallery --user someartist.bsky.social --media images --pages 10
```

---

## Code architecture

### `apitest.py` — core module + CLI

All functions are importable (no module-level side effects). `__main__` block handles CLI via `argparse`.

| Symbol | Purpose |
|---|---|
| `VERSION` | Current version string (`"1.2.0"`) |
| `CONFIG_FILE` | `Path` to `~/.config/blueskydownload/config.ini` |
| `KEY_FILE` | `Path` to `~/.config/blueskydownload/secret.key` (Fernet key, mode 600) |
| `DEFAULT_DOWNLOAD_DIR` | `~/Pictures/BlueSkyDownload` |
| `load_config()` | Reads full config (credentials + last_run sections) |
| `save_config(handle, pw)` | Read-modify-write — encrypts password before storing; preserves `[last_run]` |
| `save_ui_state(dict)` | Writes `[last_run]` section without touching credentials |
| `_get_or_create_key()` | Returns Fernet key bytes; generates + saves key file on first call |
| `encrypt_password(pw)` | Fernet-encrypt a plain-text password → base64 token string |
| `decrypt_password(token)` | Decrypt a Fernet token → plain text; returns token unchanged on failure (migration) |
| `get_app_password(cfg)` | Read + decrypt `app_password` from loaded config; returns `None` if absent |
| `bluesky_login(id, pw)` | POST `com.atproto.server.createSession` → returns session dict |
| `get_did_for_handle(handle, jwt)` | Only called for third-party targets; own DID comes from session |
| `extract_images_from_post(post)` | Returns list of `fullsize` CDN URLs |
| `extract_videos_from_post(post)` | Returns list of HLS playlist URLs |
| `format_created_at(post)` | `YYYYMMDD_HHMMSS` string from `record.createdAt` |
| `sanitize_filename(text)` | Strip non-alphanumeric chars |
| `_fetch_feed(url, params, ...)` | Shared pagination loop (tqdm, cursor, dedup) |
| `fetch_likes_media(jwt, did, ...)` | Wraps `_fetch_feed` → `getActorLikes` |
| `fetch_user_gallery(jwt, did, ...)` | Wraps `_fetch_feed` → `getAuthorFeed?filter=posts_with_media` |
| `download_media(items, dir, ...)` | Downloads images via streaming `requests`, videos via `yt-dlp`; returns stats dict |

#### `download_media` full signature

```python
def download_media(items, download_dir, media_type="both",
                   log_fn=print, error_fn=None, cancel_fn=None,
                   progress_fn=None, file_progress_fn=None, preview_fn=None,
                   delay_min=0.5, delay_max=2.0):
```

**Return value:** `{"images": N, "videos": N, "bytes": N}` — partial stats also returned on cancel.

#### `download_media` callback/delay parameters

| Parameter | Type | Purpose |
|---|---|---|
| `log_fn` | `str → None` | Normal log messages (default: `print`) |
| `error_fn` | `str → None` | Per-file error messages; defaults to `log_fn` |
| `cancel_fn` | `() → bool` | Download stops when this returns `True` |
| `progress_fn` | `(int, int) → None` | Called with `(done_count, total_count)` after each file |
| `file_progress_fn` | `(str, int, int) → None` | Called with `(filename, bytes_done, bytes_total)` during streaming |
| `preview_fn` | `str → None` | Called with the saved file path after each successful download |
| `delay_min` | `float` | Minimum seconds to sleep between posts (default: 0.5) |
| `delay_max` | `float` | Maximum seconds to sleep between posts (default: 2.0); equals `delay_min` for fixed delay |

Sleep uses `random.uniform(delay_min, delay_max)` — when min == max this is a fixed delay.
Image bytes are accumulated from the streaming download counter. Video bytes are read via
`os.path.getsize` after yt-dlp finishes (only if the file exists at the expected path).

Images are downloaded with `stream=True`; Content-Type extension fix happens before streaming starts
so the filename passed to `file_progress_fn` is always the final correct name.
`total_size=0` (no Content-Length header) signals the GUI to show an indeterminate progress bar.

tqdm is auto-disabled when `sys.stdout.isatty()` is False (GUI context).

### `gui.py` — PyQt6 frontend

Imports `apitest as bsky`. No logic lives here — only UI wiring.

#### `DownloadWorker(QThread)`

Signals:

| Signal | Signature | Purpose |
|---|---|---|
| `log` | `str` | Normal log line |
| `error` | `str` | Error log line (rendered red in GUI) |
| `done` | `(bool, str)` | Download finished: `(success, message)` |
| `progress` | `(int, int)` | `(done_count, total_count)` for overall bar |
| `file_progress` | `(str, int, int)` | `(filename, bytes_done, bytes_total)` for current-file bar |
| `preview` | `str` | File path of the latest successfully saved file |

`cancel()` sets `self._stop = True`; `download_media` checks it between posts via `cancel_fn`.

After `download_media` returns, the worker emits a summary line via `self.log`:
```
── Summary ──  Images: N  │  Videos: N  │  Total: N files  │  X.X MB
```
The `done` signal message is the compact form: `"Done — N files · X.X MB"`.

#### `MainWindow(QMainWindow)` — UI layout

```
Credentials Group      (handle, app password)
Options Group          (mode, target handle, media type, pages, post delay)
Output Folder Group    (path + Browse button)
Start / Cancel buttons
Progress Group         (total bar + count label, file bar + filename/size label)
QSplitter (horizontal, non-collapsible):
  ├── Preview Group    (QLabel — scales with panel, KeepAspectRatio)
  └── Log Group        (QTextEdit — read-only, monospace, HTML-colored)
StatusBar
```

#### Post Delay widget — `_build_delay_widget()`

Returns a `QWidget` with a `QHBoxLayout` containing:
- `cb_delay_type` (`QComboBox`): "Fixed" | "Variable"
- `dsb_delay_fixed` (`QDoubleSpinBox`, 0–60 s, default 1.0 s): visible only in Fixed mode
- `dsb_delay_min` (`QDoubleSpinBox`, 0–60 s, default 0.5 s): visible only in Variable mode
- `_lbl_delay_to` (`QLabel("to")`): visible only in Variable mode
- `dsb_delay_max` (`QDoubleSpinBox`, 0–60 s, default 2.0 s): visible only in Variable mode

`_on_delay_type_changed(mode)` toggles visibility of the fixed/variable widgets on combo change.

In `_start()`, delay values are resolved to `delay_min` / `delay_max` before passing to the worker:
- Fixed → `delay_min = delay_max = dsb_delay_fixed.value()`
- Variable → `delay_min = dsb_delay_min.value()`, `delay_max = max(dsb_delay_max.value(), delay_min)`

#### Splitter ratio — screen-responsive

Set once in `showEvent`, maintained on resize via stretch factors:

| Screen height | Preview | Log | Stretch factors |
|---|---|---|---|
| ≤ 1080 px (1080p and below) | 30 % | 70 % | 3 : 7 |
| > 1080 px (1440p, 4K, etc.) | 50 % | 50 % | 1 : 1 |

Uses `QApplication.primaryScreen().size().height()` (physical pixels).
User can still drag the splitter handle freely after launch.

#### Preview scaling

`self._current_preview_pixmap` stores the original `QPixmap`.
`_rescale_preview()` re-scales it to the label's current size with `KeepAspectRatio + SmoothTransformation`.
Called from both `_update_preview` (new file) and `resizeEvent` (window resize).
Non-image files (videos) show `"▶ Video"` text instead.

#### Config persistence

- Credentials (`handle`, `app_password`) saved to `[credentials]` on every Start click.
- UI state saved to `[last_run]` on every Start click: `mode`, `target`, `media`, `pages`, `output`,
  `delay_type`, `delay_fixed`, `delay_min`, `delay_max`.
- Both sections loaded on startup. `save_config` and `save_ui_state` both use read-modify-write
  so they never clobber each other's section.

#### Log coloring

- Normal messages: `html.escape(msg)` appended as plain text.
- Error messages: wrapped in `<span style="color: #ff5555;">…</span>`.
- `done` signal: "Cancelled." uses plain text; any other failure message uses red.

### Output filename format

```
{author_handle}_{YYYYMMDD_HHMMSS}_{post_id}_{index}.{ext}     # images
{author_handle}_{YYYYMMDD_HHMMSS}_{post_id}_v{index}.mp4      # videos
```

Image extension: parsed from `@jpeg` / `@png` suffix in CDN URL; falls back to `Content-Type` header.

---

## AT Protocol endpoints

Base URL: `https://bsky.social/xrpc/`

| Endpoint | Used for |
|---|---|
| `com.atproto.server.createSession` | Login — returns `accessJwt`, `handle`, `did` |
| `com.atproto.identity.resolveHandle` | Handle → DID (only called for third-party targets) |
| `app.bsky.feed.getActorLikes` | Liked posts feed (paginated) |
| `app.bsky.feed.getAuthorFeed` | User feed filtered to `posts_with_media` |

**Important:** `createSession` accepts email or handle as identifier. The response always contains
the resolved `handle` and `did` — these are used directly rather than calling `resolveHandle` for
the logged-in user's own account. `resolveHandle` only accepts AT handles (not emails), so it is
never called with the login identifier.

---

## Known limitations

- No cross-run deduplication beyond checking if the output filename already exists on disk.
- `yt-dlp` used as Python API — must be installed as a Python package (`yt-dlp` via pacman on Linux); bundled in the Windows exe.
- Video downloads show an indeterminate progress bar (yt-dlp gives no byte-level callback).
- Distributable AppImage (CI-built) is self-contained — no system Python or pacman deps needed. The local dev AppDir is still thin and requires pacman packages.
- Windows exe first launch may take several seconds (PyInstaller --onefile extraction to temp dir).
- `DAYS_BACK` filtering is not implemented — all paginated results are downloaded regardless of date.

---

## Security notes

The following obsolete files on disk (never committed) contain hardcoded credentials from before
the XDG config pattern was adopted. Both app passwords should be revoked in Bluesky settings:
- `apitest_backup.py`, `apitest_backup2.py`, `downloadlikes.py` — contain `oqvt-l2xw-a75k-vdzr`
- `downloadlikes.py` — also contains `ChitaChuts4099__`

All committed/tracked code is clean — no credentials in git history or any tracked file.
