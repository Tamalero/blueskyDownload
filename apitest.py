import os
import sys
import time
import random
import re
import argparse
import subprocess
import configparser
from pathlib import Path
from datetime import datetime

import requests
from tqdm import tqdm

# --- XDG paths (Arch/CachyOS) ---
_cfg_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
CONFIG_DIR = _cfg_home / "blueskydownload"
CONFIG_FILE = CONFIG_DIR / "config.ini"
DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Pictures" / "BlueSkyDownload")

# --- AT Protocol endpoints ---
_BASE = "https://bsky.social/xrpc"
LOGIN_URL    = f"{_BASE}/com.atproto.server.createSession"
RESOLVE_URL  = f"{_BASE}/com.atproto.identity.resolveHandle"
LIKES_URL    = f"{_BASE}/app.bsky.feed.getActorLikes"
GALLERY_URL  = f"{_BASE}/app.bsky.feed.getAuthorFeed"


# ── Config helpers ─────────────────────────────────────────────────────────────

def load_config():
    cfg = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        cfg.read(CONFIG_FILE)
    return cfg


def save_config(handle, app_password):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = configparser.ConfigParser()
    cfg["credentials"] = {"handle": handle, "app_password": app_password}
    with open(CONFIG_FILE, "w") as f:
        cfg.write(f)


# ── Authentication ─────────────────────────────────────────────────────────────

def bluesky_login(identifier, password):
    resp = requests.post(
        LOGIN_URL,
        json={"identifier": identifier, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_did_for_handle(handle, token):
    resp = requests.get(
        RESOLVE_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"handle": handle},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["did"]


# ── Media extraction ───────────────────────────────────────────────────────────

def extract_images_from_post(post):
    images = []
    embed = post.get("record", {}).get("embed", {})
    if embed.get("$type") == "app.bsky.embed.images":
        images.extend(embed.get("images", []))
    view_embed = post.get("embed", {})
    if view_embed.get("$type") == "app.bsky.embed.images#view":
        images.extend(view_embed.get("images", []))
    return [img["fullsize"] for img in images if "fullsize" in img]


def extract_videos_from_post(post):
    view_embed = post.get("embed", {})
    if view_embed.get("$type") == "app.bsky.embed.video#view":
        playlist = view_embed.get("playlist")
        if playlist:
            return [playlist]
    return []


def format_created_at(post):
    created_at = post.get("record", {}).get("createdAt", "")
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return dt.strftime("%Y%m%d_%H%M%S")
    except Exception:
        return "unknown_date"


def sanitize_filename(text):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text)


# ── Feed fetching ──────────────────────────────────────────────────────────────

def _fetch_feed(url, base_params, token, max_pages, page_size, log_fn):
    """Shared pagination loop for both likes and gallery endpoints."""
    headers = {"Authorization": f"Bearer {token}"}
    items, seen, cursor = [], set(), None
    tty = sys.stdout.isatty()

    with tqdm(total=max_pages, desc="Scanning", unit="pg", disable=not tty) as pbar:
        for _ in range(max_pages):
            params = {**base_params, "limit": page_size}
            if cursor:
                params["cursor"] = cursor

            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            feed = data.get("feed", [])
            if not feed:
                break

            for item in feed:
                post = item.get("post", {})
                if extract_images_from_post(post) or extract_videos_from_post(post):
                    items.append(item)

            pbar.update(1)
            pbar.set_postfix_str(f"found: {len(items)}")

            cursor = data.get("cursor")
            if not cursor or cursor in seen:
                break
            seen.add(cursor)
            time.sleep(0.2)

    log_fn(f"Found {len(items)} posts with media.")
    return items


def fetch_likes_media(token, actor_did, max_pages=25, page_size=50, log_fn=print):
    """Fetch media posts from the user's liked feed."""
    log_fn("Scanning liked posts…")
    return _fetch_feed(LIKES_URL, {"actor": actor_did}, token, max_pages, page_size, log_fn)


def fetch_user_gallery(token, actor_did, max_pages=25, page_size=50, log_fn=print):
    """Fetch media posts from a user's gallery (their posts_with_media feed)."""
    log_fn("Scanning user gallery…")
    return _fetch_feed(
        GALLERY_URL,
        {"actor": actor_did, "filter": "posts_with_media"},
        token, max_pages, page_size, log_fn,
    )


# ── Downloading ────────────────────────────────────────────────────────────────

def _download_video(url, output_template):
    subprocess.run(
        ["yt-dlp", "-f", "bestvideo+bestaudio/best",
         "--merge-output-format", "mp4", "-o", output_template, url],
        check=True,
    )


def download_media(items, download_dir, media_type="both",
                   log_fn=print, cancel_fn=None):
    """
    Download images and/or videos from a list of feed items.

    media_type: "images" | "videos" | "both"
    cancel_fn:  optional callable; download stops when it returns True
    """
    os.makedirs(download_dir, exist_ok=True)
    tty = sys.stdout.isatty()

    for item in tqdm(items, desc="Downloading", unit="post", disable=not tty):
        if cancel_fn and cancel_fn():
            log_fn("Download cancelled.")
            return

        post   = item.get("post", {})
        handle = sanitize_filename(post.get("author", {}).get("handle", "unknown"))
        uri    = post.get("uri", "")
        pid    = sanitize_filename(uri.rsplit("/", 1)[-1]) if uri else "nopostid"
        ts     = format_created_at(post)

        if media_type in ("images", "both"):
            for i, img_url in enumerate(extract_images_from_post(post), 1):
                ext   = img_url.split("@")[-1].split("?")[0] if "@" in img_url else "jpg"
                fname = f"{handle}_{ts}_{pid}_{i}.{ext}"
                fpath = os.path.join(download_dir, fname)
                if os.path.exists(fpath):
                    continue
                try:
                    r = requests.get(img_url, timeout=30)
                    r.raise_for_status()
                    # Correct extension from Content-Type when URL has no @ext suffix
                    if "@" not in img_url:
                        ct  = r.headers.get("Content-Type", "image/jpeg")
                        ext = ct.split("/")[-1].split(";")[0].strip()
                        fname = f"{handle}_{ts}_{pid}_{i}.{ext}"
                        fpath = os.path.join(download_dir, fname)
                    with open(fpath, "wb") as f:
                        f.write(r.content)
                    log_fn(f"Saved image: {fname}")
                except Exception as e:
                    log_fn(f"Image failed: {e}")

        if media_type in ("videos", "both"):
            for i, vid_url in enumerate(extract_videos_from_post(post), 1):
                out_tpl = os.path.join(download_dir, f"{handle}_{ts}_{pid}_v{i}.%(ext)s")
                try:
                    _download_video(vid_url, out_tpl)
                    log_fn(f"Saved video: {handle}_{ts}_{pid}_v{i}.mp4")
                except Exception as e:
                    log_fn(f"Video failed: {e}")

        time.sleep(random.uniform(0.5, 2.0))


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BlueSky media downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  likes    Download media from your (or another user's) liked posts
  gallery  Download media from a user's profile gallery

Examples:
  python apitest.py --mode likes
  python apitest.py --mode gallery --user someartist.bsky.social
  python apitest.py --mode gallery --user someartist.bsky.social --media images --pages 10
        """,
    )
    parser.add_argument("--mode",   choices=["likes", "gallery"], default="likes")
    parser.add_argument("--user",   metavar="HANDLE",
                        help="Target handle (default: your own account)")
    parser.add_argument("--media",  choices=["images", "videos", "both"], default="both")
    parser.add_argument("--pages",  type=int, default=25, metavar="N",
                        help="Max pages to scan — 50 posts per page (default: 25)")
    parser.add_argument("--output", metavar="DIR", default=DEFAULT_DOWNLOAD_DIR)
    parser.add_argument("--handle", metavar="HANDLE", help="Your Bluesky handle")
    parser.add_argument("--password", metavar="PASSWORD", help="Your Bluesky app password")
    args = parser.parse_args()

    cfg = load_config()
    my_handle   = args.handle   or cfg.get("credentials", "handle",       fallback=None)
    my_password = args.password or cfg.get("credentials", "app_password", fallback=None)

    if not my_handle or not my_password:
        print("Error: credentials not found.")
        print(f"  Configure {CONFIG_FILE}:")
        print("  [credentials]")
        print("  handle = yourname.bsky.social")
        print("  app_password = xxxx-xxxx-xxxx-xxxx")
        print()
        print("  Or pass --handle and --password on the command line.")
        sys.exit(1)

    print(f"Logging in as {my_handle}…")
    try:
        session = bluesky_login(my_handle, my_password)
    except Exception as e:
        print(f"Login failed: {e}")
        if "401" in str(e) or "Unauthorized" in str(e):
            print("Tip: if your handle gives 401, try logging in with your email address instead.")
        sys.exit(1)

    jwt = session["accessJwt"]
    # session always contains the resolved handle and DID regardless of whether
    # the user logged in with an email address or a .bsky.social handle
    my_actual_handle = session["handle"]
    my_did           = session["did"]

    if args.user:
        target = args.user
        print(f"Resolving {target}…")
        target_did = get_did_for_handle(target, jwt)
    else:
        target     = my_actual_handle
        target_did = my_did  # already in the session, no extra API call needed

    if args.mode == "likes":
        print(f"Mode: liked posts of {target}")
        items = fetch_likes_media(jwt, target_did, max_pages=args.pages)
    else:
        print(f"Mode: gallery of {target}")
        items = fetch_user_gallery(jwt, target_did, max_pages=args.pages)

    print(f"Downloading {len(items)} posts → {args.output}")
    download_media(items, args.output, media_type=args.media)
    print("Done.")
