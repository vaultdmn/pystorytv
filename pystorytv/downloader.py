"""Download engine — wraps yt-dlp to fetch and mux HLS streams."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable, Optional
import concurrent.futures

from pystorytv.models import Episode


def _sanitize_filename(name: str) -> str:
    """Remove characters invalid in filenames and fix trailing spaces/dots."""
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
    return sanitized.strip(" .")


class Downloader:
    def __init__(self, max_workers: int = 0):
        self.max_workers = max_workers

    def show_episode_info(self, episode: Episode) -> None:
        """Print available formats using yt-dlp."""
        try:
            import yt_dlp
        except ImportError:
            print("yt-dlp not installed.", file=sys.stderr)
            return
            
        ydl_opts = {
            "listformats": True,
            "quiet": False,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.extract_info(episode.eps_url, download=False)
            except Exception as e:
                print(f"Error fetching formats: {e}", file=sys.stderr)

    def download_episode(
        self,
        episode: Episode,
        show_title: str,
        output_dir: Path,
        quality: str = "best",
        lang: Optional[str] = None,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> Path:
        """
        Download a single episode using yt-dlp.
        """
        try:
            import yt_dlp
        except ImportError:
            raise ImportError("yt-dlp is required. Install with: pip install yt-dlp")

        output_dir.mkdir(parents=True, exist_ok=True)

        ep_label = f"E{episode.index:02d}"
        safe_show = _sanitize_filename(show_title)
        safe_title = _sanitize_filename(episode.eps_title)
        filename = f"{safe_show} - {ep_label} - {safe_title}"
        outtmpl = str(output_dir / f"{filename}.%(ext)s")

        last_pct = [0.0]

        def _progress_hook(d: dict) -> None:
            if d["status"] == "downloading" and on_progress:
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    pct = downloaded / total
                    if abs(pct - last_pct[0]) >= 0.01:
                        last_pct[0] = pct
                        on_progress(pct)

        fmt = quality if quality != "best" else None
        if lang:
            fmt = f"bestvideo+bestaudio[language={lang}]/bestvideo+bestaudio[format_id*={lang}]/best"
            
        ydl_opts: dict = {
            "format": fmt,
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
            "progress_hooks": [_progress_hook],
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ],
            "hls_prefer_native": False,
            "external_downloader_args": {"ffmpeg_i": ["-reconnect", "1"]},
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([episode.eps_url])

        for ext in ("mp4", "mkv", "ts", "m4v"):
            candidate = output_dir / f"{filename}.{ext}"
            if candidate.exists():
                return candidate

        matches = list(output_dir.glob(f"{filename}.*"))
        if matches:
            return matches[0]

        raise FileNotFoundError(f"Download finished but output file not found in {output_dir}")

    def download_bulk(
        self,
        episodes: list[Episode],
        show_title: str,
        output_dir: Path,
        quality: str = "best",
        lang: Optional[str] = None,
        on_task_start: Optional[Callable[[Episode], None]] = None,
        on_task_progress: Optional[Callable[[Episode, float], None]] = None,
        on_task_complete: Optional[Callable[[Episode, Path], None]] = None,
        on_task_error: Optional[Callable[[Episode, Exception], None]] = None,
    ) -> list[Path]:
        """Download a batch of episodes, optionally in parallel."""
        downloaded: list[Path] = []
        if not episodes:
            return downloaded

        output_dir.mkdir(parents=True, exist_ok=True)

        def _download_task(ep: Episode) -> Optional[Path]:
            if on_task_start:
                on_task_start(ep)

            def _on_progress(pct: float) -> None:
                if on_task_progress:
                    on_task_progress(ep, pct)

            try:
                path = self.download_episode(
                    ep, show_title, output_dir, quality=quality, lang=lang, on_progress=_on_progress
                )
                if on_task_complete:
                    on_task_complete(ep, path)
                return path
            except Exception as exc:
                if on_task_error:
                    on_task_error(ep, exc)
                return None

        if self.max_workers > 0:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = list(executor.map(_download_task, episodes))
                for res in results:
                    if res:
                        downloaded.append(res)
        else:
            for ep in episodes:
                res = _download_task(ep)
                if res:
                    downloaded.append(res)

        return downloaded


def list_formats(url: str) -> list[dict]:
    """
    List available stream formats/qualities for an m3u8 URL.
    Returns yt-dlp format dictionaries.
    """
    try:
        import yt_dlp
    except ImportError:
        raise ImportError("yt-dlp is required. Install with: pip install yt-dlp")

    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("formats", []) if info else []
