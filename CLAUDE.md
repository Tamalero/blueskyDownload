# BlueSkyDownload — Claude Context

## Project at a glance

Personal Python tool to download media (images + videos) from Bluesky using the AT Protocol REST API.
Two entry points: a CLI (`apitest.py`) and a PyQt6 GUI (`gui.py`).

- **GitHub:** https://github.com/Tamalero/blueskyDownload  
- **Platform:** Arch/CachyOS, x86_64  
- **Python:** system Python 3 (no virtualenv — all deps via pacman)  
- **XDG config:** `~/.config/blueskydownload/config.ini`  
- **Default output:** `~/Pictures/BlueSkyDownload`

---

## Repository state (as of 2025-05-05)

Git is initialized. Remote is `https://github.com/Tamalero/blueskyDownload.git`, branch `main`.

Committed files:

```
.gitignore
CLAUDE.md
README.md
apitest.py            ← main CLI + shared library
gui.py                ← PyQt6 GUI (imports apitest)
blueskydownload.desktop
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
| `python-tqdm` | installed (added this session) |
| `python-pyqt6` | installed |
| `yt-dlp` | installed |
| `ffmpeg` | installed |
| `appimagetool-bin` | installed (added this session, AUR) |

---

## AppImage

A Type 2 AppImage was built:

```
BlueSkyDownloader-x86_64.AppImage   (939 KB, squashfs/zstd, ELF runtime)
```

Located in the project directory. Not committed to git (excluded by `.gitignore`).
Should be attached to a GitHub Release manually if distribution is needed.

AppDir structure used:
```
BlueSkyDownloader.AppDir/
├── AppRun                  (bash launcher → python3 usr/bin/gui.py)
├── blueskydownload.desktop (Exec=blueskydownloader, Icon=blueskydownload)
├── blueskydownload.png     (256×256, blue #0085ff with "BSky" text, imagemagick)
└── usr/bin/
    ├── apitest.py
    └── gui.py
```

The AppImage is thin — it bundles only the Python scripts and uses system Python/pacman packages.
Rebuild command:
```bash
ARCH=x86_64 appimagetool BlueSkyDownloader.AppDir BlueSkyDownloader-x86_64.AppImage
```

---

## Desktop launcher

`blueskydownload.desktop` is in the project root and committed to git.
It is **not yet installed** to `~/.local/share/applications/` (user declined during this session).

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
| `CONFIG_FILE` | `Path` to `~/.config/blueskydownload/config.ini` |
| `DEFAULT_DOWNLOAD_DIR` | `~/Pictures/BlueSkyDownload` |
| `load_config()` / `save_config()` | XDG config read/write |
| `bluesky_login(id, pw)` | POST `com.atproto.server.createSession` → returns session dict |
| `get_did_for_handle(handle, jwt)` | Resolve handle → DID string |
| `extract_images_from_post(post)` | Returns list of `fullsize` CDN URLs |
| `extract_videos_from_post(post)` | Returns list of HLS playlist URLs |
| `format_created_at(post)` | `YYYYMMDD_HHMMSS` string from `record.createdAt` |
| `sanitize_filename(text)` | Strip non-alphanumeric chars |
| `_fetch_feed(url, params, ...)` | Shared pagination loop (tqdm, cursor, dedup) |
| `fetch_likes_media(jwt, did, ...)` | Wraps `_fetch_feed` → `getActorLikes` |
| `fetch_user_gallery(jwt, did, ...)` | Wraps `_fetch_feed` → `getAuthorFeed?filter=posts_with_media` |
| `download_media(items, dir, ...)` | Downloads images via `requests`, videos via `yt-dlp` subprocess |

`fetch_*` and `download_media` accept:
- `log_fn=print` — replaced by `self.log.emit` in the GUI worker
- `cancel_fn=None` — GUI passes `lambda: self._stop` for the cancel button

tqdm is auto-disabled when stdout is not a tty (i.e. when called from the GUI thread).

### `gui.py` — PyQt6 frontend

Imports `apitest as bsky`. No logic lives here — only UI wiring.

`DownloadWorker(QThread)`:
- `run()` calls `bsky.bluesky_login → get_did_for_handle → fetch_* → download_media`
- Emits `log(str)` and `done(bool, str)` signals
- `cancel()` sets `self._stop = True`; `download_media` checks it between posts

`MainWindow(QMainWindow)`:
- Credentials auto-loaded from XDG config on startup via `bsky.load_config()`
- Credentials saved on every Start click via `bsky.save_config()`
- Mode dropdown: `"Liked Posts"` / `"User Gallery"`
- Media dropdown: `"Both"` / `"Images Only"` / `"Videos Only"`
- Pages spinbox: 1–200, default 25

### Output filename format

```
{author_handle}_{YYYYMMDD_HHMMSS}_{post_id}_{index}.{ext}     # images
{author_handle}_{YYYYMMDD_HHMMSS}_{post_id}_v{index}.mp4      # videos
```

Image extension is parsed from the `@jpeg` / `@png` suffix in the CDN URL, with a fallback to the
`Content-Type` response header.

---

## AT Protocol endpoints

Base URL: `https://bsky.social/xrpc/`

| Endpoint | Used for |
|---|---|
| `com.atproto.server.createSession` | Login, returns `accessJwt` |
| `com.atproto.identity.resolveHandle` | Handle → DID |
| `app.bsky.feed.getActorLikes` | Liked posts feed (paginated) |
| `app.bsky.feed.getAuthorFeed` | User feed filtered to `posts_with_media` |

---

## Known limitations

- No cross-run deduplication beyond checking if the output filename already exists on disk.
- `yt-dlp` invoked as a subprocess — must be on `PATH`.
- Bluesky rate limits not explicitly handled; 0.5–2 s random delay between posts is a soft guard.
- `DAYS_BACK` constant exists in old backups but is not implemented in the current script — all
  paginated results are downloaded regardless of date.
- AppImage is a thin wrapper — target machine must have `python-pyqt6`, `python-requests`,
  `python-tqdm`, `yt-dlp` installed.
