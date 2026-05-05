# BlueSky Downloader

A Python tool to download images and videos from [Bluesky](https://bsky.app) — from your liked posts or any user's gallery.

Available as a **GUI app**, a **CLI tool**, and a portable **AppImage** for Arch/CachyOS.

---

## Features

- Download all **images and/or videos** from your liked posts
- Download media from **any user's gallery** (their public media tab)
- Filter by media type: images, videos, or both
- Configurable page depth (up to 200 pages × 50 posts)
- **Download summary** on completion — images, videos, total files, total MB
- **Configurable post delay** — fixed timing or random range (min–max) to avoid rate limiting
- Skips files already on disk — safe to re-run
- Live file progress bar with filename and byte-level size display
- Overall progress bar with file count
- Latest downloaded image shown as a live preview thumbnail
- Error messages highlighted in red in the log
- Saves and restores last-run options between sessions
- Credentials stored in `~/.config/blueskydownload/config.ini` (XDG standard)
- Downloads saved to `~/Pictures/BlueSkyDownload` by default

---

## Requirements

### Windows
Download `BlueSkyDownloader.exe` from [Releases](https://github.com/Tamalero/blueskyDownload/releases) — no Python or dependencies needed.

For **video downloads**, install `yt-dlp` and add it to your PATH:
```
winget install yt-dlp.yt-dlp
winget install Gyan.FFmpeg
```
Images download without them.

### Linux (Arch/CachyOS)
Install dependencies via pacman:

```bash
sudo pacman -S python-requests python-tqdm python-pyqt6 yt-dlp ffmpeg
```

> `yt-dlp` and `ffmpeg` are only needed for video downloads. Images work without them.

---

## Setup

Generate an **App Password** on Bluesky:  
**Settings → Privacy and Security → App Passwords**

On first run, enter your handle and app password in the GUI — they'll be saved automatically.

For CLI-only use, create the config file manually:

```bash
mkdir -p ~/.config/blueskydownload
cat > ~/.config/blueskydownload/config.ini << EOF
[credentials]
handle = yourname.bsky.social
app_password = xxxx-xxxx-xxxx-xxxx
EOF
```

---

## Usage

### GUI

```bash
python gui.py
```

Select your mode, target handle, media type, output folder, and post delay, then click **Start Download**.

When the download finishes, a summary is shown in the log:

```
── Summary ──  Images: 42  │  Videos: 3  │  Total: 45 files  │  128.4 MB
```

#### Post Delay option

| Mode | Behaviour |
|------|-----------|
| **Fixed** | Waits exactly N seconds between posts |
| **Variable** | Waits a random duration between Min and Max seconds |

Default is Variable 0.5–2.0 s. Set to 0 s (fixed) to disable all delays.

### CLI

```bash
# Download your liked posts (images + videos)
python apitest.py --mode likes

# Download a specific user's gallery (images only)
python apitest.py --mode gallery --user someartist.bsky.social --media images

# Full options
python apitest.py --help
```

**Available flags:**

| Flag | Options | Default |
|------|---------|---------|
| `--mode` | `likes` / `gallery` | `likes` |
| `--user` | any Bluesky handle | your own account |
| `--media` | `images` / `videos` / `both` | `both` |
| `--pages` | 1–200 | `25` (50 posts/page) |
| `--output` | directory path | `~/Pictures/BlueSkyDownload` |
| `--handle` | your handle | from config |
| `--password` | your app password | from config |

### Windows Executable

Download `BlueSkyDownloader.exe` from [Releases](https://github.com/Tamalero/blueskyDownload/releases) and double-click to run. No installation required.

> First launch may take a few seconds while the app unpacks itself.

### AppImage (Arch/CachyOS)

Download `BlueSkyDownloader-x86_64.AppImage` from [Releases](https://github.com/Tamalero/blueskyDownload/releases), then:

```bash
chmod +x BlueSkyDownloader-x86_64.AppImage
./BlueSkyDownloader-x86_64.AppImage
```

#### Auto-update

```bash
AppImageUpdate BlueSkyDownloader-x86_64.AppImage
```

Requires [AppImageUpdate](https://github.com/AppImageCommunity/AppImageUpdate). The AppImage contains embedded update metadata pointing to the latest GitHub release.

---

## Output

Files are saved as:

```
{author_handle}_{YYYYMMDD_HHMMSS}_{post_id}_{index}.{ext}
```

Example: `someartist_20240315_143022_3ld5abc_1.jpeg`  
Videos: `someartist_20240315_143022_3ld5abc_v1.mp4`

---

## Desktop Integration (Arch/CachyOS)

Register the app in your application menu:

```bash
cp blueskydownload.desktop ~/.local/share/applications/
# Edit the Exec line to point to the absolute path of gui.py
```

---

## How It Works

Uses the [Bluesky AT Protocol](https://atproto.com/) REST API directly — no browser automation or scraping.

| Mode | Endpoint |
|------|----------|
| Liked posts | `app.bsky.feed.getActorLikes` |
| User gallery | `app.bsky.feed.getAuthorFeed?filter=posts_with_media` |

Videos are downloaded via `yt-dlp` using the HLS playlist URL exposed by the API.

---

## Changelog

### v1.1.0
- Download summary on completion: images count, videos count, total files, total size in MB/KB
- Configurable post delay: Fixed (single value) or Variable (random min–max range)
- Delay setting is saved and restored between sessions
- Windows 11 compatible standalone `.exe` (via GitHub Actions / PyInstaller)

### v1.0.0
- Initial release
- GUI with overall and per-file progress bars, live preview, colored error log
- Liked posts and user gallery download modes
- Image and video support via `yt-dlp`
- Saved credentials and last-run UI state
- AppImage with embedded auto-update metadata

---

## License

Personal use. No warranty.
