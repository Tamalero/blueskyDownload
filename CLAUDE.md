# BlueSkyDownload

A personal Python toolset for downloading liked images and videos from Bluesky (bsky.social) using the AT Protocol API.

## Project Purpose

Downloads media (images and videos) from:
- A user's **liked posts** feed
- Any user's **gallery** (their posts that contain media)

---

## File Overview

### Active

| File | Description |
|---|---|
| `apitest.py` | Core logic + CLI entry point. AT Protocol API calls, media extraction, downloading. |
| `gui.py` | PyQt6 GUI entry point. Imports from `apitest.py`. Runs downloads in a background thread. |
| `blueskydownload.desktop` | FreeDesktop app launcher for Arch/CachyOS. |
| `config.ini` | Legacy local config (credentials superseded by XDG path — see below). |

### Obsolete / Archive

Earlier iterations kept for reference only.

| File | Description |
|---|---|
| `apitest_backup.py` | API version — images only, no video. |
| `apitest_backup2.py` | Used `atproto` SDK; images only. |
| `downloadlikes.py` | Bearer token prototype; thumbnail downloads only. |
| `singledownload.py` | Selenium-based; intercepted HLS `.m3u8` streams via Chrome perf logs. |
| `generic.py` | Incomplete Selenium skeleton. |
| `newversion.py` | `yt-dlp` batch downloader via `urls.txt` + `credentials.txt`. |
| `newcookies.py` | `yt-dlp` batch downloader via Netscape `cookies.txt`. |
| `logintest.py` | Login scratch script. |
| `test.py` | General scratch file. |

---

## Running

### GUI

```bash
python gui.py
```

### CLI

```bash
# Download your liked posts (images + videos)
python apitest.py --mode likes

# Download a user's gallery (images only, 10 pages)
python apitest.py --mode gallery --user someartist.bsky.social --media images --pages 10

# Full options
python apitest.py --help
```

### CLI flags

| Flag | Values | Default |
|---|---|---|
| `--mode` | `likes` / `gallery` | `likes` |
| `--user` | any Bluesky handle | your own account |
| `--media` | `images` / `videos` / `both` | `both` |
| `--pages` | 1–200 | 25 (50 posts/page) |
| `--output` | directory path | `~/Pictures/BlueSkyDownload` |
| `--handle` | your handle | from config |
| `--password` | your app password | from config |

---

## Credentials & Config

Credentials are stored at **`~/.config/blueskydownload/config.ini`** (XDG standard).

The GUI saves credentials automatically on first successful run. For CLI-only use, create the file manually:

```ini
[credentials]
handle = yourname.bsky.social
app_password = xxxx-xxxx-xxxx-xxxx
```

App passwords are generated in Bluesky: **Settings → Privacy and Security → App Passwords**.

**Do not commit credentials to any repository.**

---

## Dependencies

All available via pacman on Arch/CachyOS:

```bash
sudo pacman -S python-requests python-tqdm python-pyqt6 yt-dlp ffmpeg
```

`yt-dlp` and `ffmpeg` must be on `PATH` for video downloads. Images work without them.

For pip (alternative):

```bash
pip install requests tqdm PyQt6
```

---

## Desktop Launcher (Arch/CachyOS)

To register the app in your application menu:

```bash
cp blueskydownload.desktop ~/.local/share/applications/
# then edit the Exec line to use the absolute path to gui.py
```

---

## Architecture

### `apitest.py` — core module

All functions are importable (no top-level side effects). The `if __name__ == "__main__"` block handles CLI.

| Function | Purpose |
|---|---|
| `load_config()` / `save_config()` | XDG config read/write |
| `bluesky_login(handle, password)` | POST to `com.atproto.server.createSession` |
| `get_did_for_handle(handle, token)` | Resolve handle → DID |
| `fetch_likes_media(token, did, ...)` | Paginate `app.bsky.feed.getActorLikes` |
| `fetch_user_gallery(token, did, ...)` | Paginate `app.bsky.feed.getAuthorFeed?filter=posts_with_media` |
| `download_media(items, dir, ...)` | Download images via `requests`, videos via `yt-dlp` subprocess |

Both fetch functions accept `log_fn=` (callable for status messages) used by the GUI to pipe output to the log widget.

`download_media` accepts `cancel_fn=` (callable returning bool) used by the GUI cancel button.

### `gui.py` — PyQt6 frontend

`DownloadWorker(QThread)` runs the download in a background thread, emitting:
- `log(str)` — appended to the log widget
- `done(bool, str)` — re-enables controls and updates the status bar

### Output Filename Format

```
{author_handle}_{YYYYMMDD_HHMMSS}_{post_id}_{index}.{ext}
```

Example: `someartist_20240315_143022_3ld5abc_1.jpeg`

Videos: same pattern with `_v{index}.mp4`.

---

## AT Protocol Endpoints Used

| Endpoint | Purpose |
|---|---|
| `com.atproto.server.createSession` | Login → JWT |
| `com.atproto.identity.resolveHandle` | Handle → DID |
| `app.bsky.feed.getActorLikes` | Liked posts feed |
| `app.bsky.feed.getAuthorFeed` | User's own posts (filtered to media) |

Base: `https://bsky.social/xrpc/`

---

## Known Limitations

- No cross-run deduplication beyond checking if the output file already exists on disk.
- `yt-dlp` is called as a subprocess (not library) — requires it on `PATH`.
- Bluesky rate limits are not explicitly handled; the 0.5–2s delay between posts is a soft guard.
