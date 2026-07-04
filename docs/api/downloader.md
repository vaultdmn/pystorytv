# Downloader

The `Downloader` class wraps `yt-dlp` and `ffmpeg` to download HLS (`.m3u8`) streams seamlessly and convert them to standard `.mp4` files.

```python
from pystorytv.downloader import Downloader
from pathlib import Path

downloader = Downloader(max_workers=5)
```

## Methods

### `download_episode(episode, show_title, output_dir, quality="best", lang=None, on_progress=None)`
Downloads a single episode.

* `episode`: An `Episode` object obtained from the client.
* `show_title`: Used to format the filename (`Show Name - E01 - Title.mp4`).
* `output_dir`: A `pathlib.Path` pointing to the destination folder.
* `on_progress`: A callback function `func(pct: float)` that will be fired as the download progresses (0.0 to 1.0).

### `download_bulk(episodes, show_title, output_dir, ...)`
Downloads a list of episodes. If `max_workers > 0` was passed to the `Downloader` constructor, these will be downloaded in parallel!

```python
from pathlib import Path

def print_progress(ep, pct):
    print(f"Episode {ep.index} is at {pct*100:.1f}%")

downloader.download_bulk(
    episodes=episodes_list,
    show_title=show.title,
    output_dir=Path("./MyShow"),
    on_task_progress=print_progress
)
```

**Callbacks available in `download_bulk`:**
* `on_task_start(ep)`
* `on_task_progress(ep, pct)`
* `on_task_complete(ep, path)`
* `on_task_error(ep, exception)`
