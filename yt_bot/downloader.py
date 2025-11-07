"""Core download logic for the YouTube bot."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import yt_dlp

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DownloadRequest:
    """Parameters that control a download session."""

    urls: Sequence[str]
    output_dir: Path = Path("downloads")
    audio_only: bool = False
    embed_thumbnail: bool = True
    filename_template: str = "%(title)s [%(id)s].%(ext)s"
    restrict_filenames: bool = True
    extra_ytdlp_options: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DownloadResult:
    """Holds information about the outcome of a download session."""

    filepaths: List[Path] = field(default_factory=list)
    infos: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Return ``True`` if every item downloaded successfully."""

        return not self.errors


class YouTubeDownloader:
    """Download helper that wraps :mod:`yt_dlp`."""

    def __init__(self, *, logger_name: str | None = None) -> None:
        if logger_name:
            self._logger = logging.getLogger(logger_name)
        else:
            self._logger = logger

    def download(self, request: DownloadRequest) -> DownloadResult:
        """Download the requested URLs at the highest available quality."""

        if not request.urls:
            raise ValueError("At least one URL must be provided")

        output_dir = request.output_dir.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        progress_filepaths: List[Path] = []

        def _progress_hook(status: Dict[str, Any]) -> None:
            if status.get("status") == "finished" and status.get("filename"):
                progress_filepaths.append(Path(status["filename"]).resolve())
                self._logger.info("Finished downloading %s", status["filename"])

        options = self._build_ytdlp_options(request, output_dir, _progress_hook)
        result = DownloadResult()

        with yt_dlp.YoutubeDL(options) as ydl:
            for url in request.urls:
                try:
                    info = ydl.extract_info(url, download=True)
                except yt_dlp.utils.DownloadError as err:
                    error_message = str(err)
                    self._logger.error("Failed to download %s: %s", url, error_message)
                    result.errors.append(error_message)
                    continue

                if info is None:
                    message = f"No information was returned for URL: {url}"
                    self._logger.error(message)
                    result.errors.append(message)
                    continue

                result.infos.extend(_flatten_entries(info))

        # Deduplicate paths while preserving order
        seen: set[Path] = set()
        for filepath in progress_filepaths:
            if filepath not in seen:
                result.filepaths.append(filepath)
                seen.add(filepath)

        return result

    def _build_ytdlp_options(
        self,
        request: DownloadRequest,
        output_dir: Path,
        progress_hook: Any,
    ) -> Dict[str, Any]:
        postprocessors: List[Dict[str, Any]] = []
        format_selector = "bv*+ba/b"

        if request.audio_only:
            format_selector = "bestaudio/best"
            postprocessors.append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            )

        if request.embed_thumbnail:
            postprocessors.extend(
                [
                    {"key": "EmbedThumbnail"},
                    {"key": "FFmpegMetadata"},
                ]
            )

        options: Dict[str, Any] = {
            "format": format_selector,
            "merge_output_format": "mp4",
            "outtmpl": str(output_dir / request.filename_template),
            "restrictfilenames": request.restrict_filenames,
            "ignoreerrors": True,
            "nocheckcertificate": True,
            "progress_hooks": [progress_hook],
            "postprocessors": postprocessors,
            "concurrent_fragment_downloads": 4,
            "writethumbnail": request.embed_thumbnail,
            "noplaylist": False,
            "quiet": False,
            "no_warnings": True,
        }

        options.update(request.extra_ytdlp_options)
        return options


def _flatten_entries(info: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Normalize playlist and single video responses to a flat iterable."""

    if "entries" in info and isinstance(info["entries"], list):
        for entry in info["entries"]:
            if entry:
                yield entry
    else:
        yield info
