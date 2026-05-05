# BlueSky Downloader

A Python tool to download images and videos from [Bluesky](https://bsky.app) — from your liked posts or any user's gallery.

Available as a **GUI app**, a **CLI tool**, and a portable **AppImage** for Arch/CachyOS.

---

## Features

- Download all **images and/or videos** from your liked posts
- Download media from **any user's gallery** (their public media tab)
- Filter by media type: images, videos, or both
- Configurable page depth (up to 200 pages × 50 posts)
- Skips files already on disk — safe to re-run
- Credentials stored in `~/.config/blueskydownload/config.ini` (XDG standard)
- Downloads saved to `~/Pictures/BlueSkyDownload` by default

---

## Requirements

Install dependencies via pacman on Arch/CachyOS:

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

![GUI screenshot placeholder](https://via.placeholder.com/560x420?text=BlueSky+Downloader+GUI)

Select your mode, target handle, media type, and output folder, then click **Start Download**.

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

### AppImage (Arch/CachyOS)

Download `BlueSkyDownloader-x86_64.AppImage` from [Releases](https://github.com/Tamalero/blueskyDownload/releases), then:

```bash
chmod +x BlueSkyDownloader-x86_64.AppImage
./BlueSkyDownloader-x86_64.AppImage
```

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

## License

Personal use. No warranty.
