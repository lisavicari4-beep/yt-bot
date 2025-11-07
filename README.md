# yt-bot

A high quality YouTube video (and audio) download bot built on top of [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Features

- Downloads at the best available video quality (`bestvideo+bestaudio`).
- Optional audio-only mode that extracts high bitrate MP3 files.
- Embeds thumbnails and metadata using FFmpeg post-processing (configurable).
- Supports playlists, URL lists from files, and duplicate URL deduplication.
- CLI with helpful logging and exit codes for automation.

## Requirements

- Python 3.9+
- [FFmpeg](https://ffmpeg.org/) (required for muxing, thumbnail embedding, and audio extraction)
- Dependencies from `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Download a single video at the highest quality:

```bash
python -m yt_bot https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Download only the audio and store it in a custom directory:

```bash
python -m yt_bot --audio-only --output-dir music \
  https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Download multiple URLs from a text file while disabling thumbnail embedding:

```bash
python -m yt_bot --urls-file urls.txt --no-embed-thumbnail
```

Use `--help` to view all available options:

```bash
python -m yt_bot --help
```

## Programmatic usage

```python
from pathlib import Path

from yt_bot import DownloadRequest, YouTubeDownloader

request = DownloadRequest(
    urls=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    output_dir=Path("downloads"),
)

downloader = YouTubeDownloader()
result = downloader.download(request)

if result.success:
    print("Downloaded:", result.filepaths)
else:
    print("Errors:", result.errors)
```
