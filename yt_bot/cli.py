"""Command line interface for the YouTube download bot."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Iterable, List

from .downloader import DownloadRequest, YouTubeDownloader


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Download YouTube videos or audio in the best available quality using yt-dlp."
        )
    )
    parser.add_argument("urls", nargs="*", help="Video or playlist URLs to download.")
    parser.add_argument(
        "--urls-file",
        type=Path,
        help="Optional path to a text file containing one URL per line.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("downloads"),
        help="Directory where files will be saved (default: ./downloads).",
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Download audio only (converted to high quality MP3).",
    )
    parser.add_argument(
        "--no-embed-thumbnail",
        action="store_true",
        help="Disable embedding thumbnails into the downloaded files.",
    )
    parser.add_argument(
        "--allow-unsafe-filenames",
        action="store_true",
        help="Do not restrict file names to ASCII-safe characters.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity level (default: INFO).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="yt-bot 1.0",
        help="Show program's version number and exit.",
    )
    return parser


def parse_urls(urls: Iterable[str], urls_file: Path | None) -> List[str]:
    collected = list(urls)

    if urls_file:
        try:
            lines = urls_file.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError as err:
            raise SystemExit(f"Could not read URLs file: {err}") from err

        collected.extend(line.strip() for line in lines if line.strip())

    unique_urls: List[str] = []
    seen = set()
    for url in collected:
        if url not in seen:
            unique_urls.append(url)
            seen.add(url)
    return unique_urls


def run_cli(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="[%(levelname)s] %(message)s",
    )

    urls = parse_urls(args.urls, args.urls_file)
    if not urls:
        parser.error("Please provide at least one YouTube URL or a file containing URLs.")

    downloader = YouTubeDownloader()
    request = DownloadRequest(
        urls=urls,
        output_dir=args.output_dir,
        audio_only=args.audio_only,
        embed_thumbnail=not args.no_embed_thumbnail,
        restrict_filenames=not args.allow_unsafe_filenames,
    )

    result = downloader.download(request)

    if result.success:
        for path in result.filepaths:
            print(f"Saved: {path}")
        return 0

    for error in result.errors:
        print(f"Error: {error}", file=sys.stderr)
    if result.filepaths:
        for path in result.filepaths:
            print(f"Saved (with errors): {path}")
    return 1


def main() -> None:
    sys.exit(run_cli())


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
