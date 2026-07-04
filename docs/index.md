# pystorytv

[![PyPI version](https://badge.fury.io/py/pystorytv.svg)](https://badge.fury.io/py/pystorytv)
[![Documentation](https://img.shields.io/badge/docs-pystorytv.vrma.dev-blue.svg)](https://pystorytv.vrma.dev)

A complete Python API wrapper for [StoryTV](https://storytv.asia).

Browse, search, stream, and bulk-download Hindi/regional dramas effortlessly from within your own Python programs.

## Features

- **Python API** — Object-oriented wrapper around StoryTV endpoints.
- **Bulk Downloader** — Thread-pool based parallel downloading of m3u8 streams via `yt-dlp` and `ffmpeg`.
- **OTPLess Login** — Phone OTP authentication, session handled automatically.

## Requirements

- Python 3.10+
- `ffmpeg` (required for downloading/muxing HLS streams)

## Installation

Install from PyPI:

```bash
pip install pystorytv
```

## Quick Start (Python API)

```python
from pystorytv import AuthManager, StoryTVClient
from pystorytv.downloader import Downloader

# 1. Authenticate
auth = AuthManager()
if not auth.is_logged_in():
    auth.request_otp("9876543210", "+91")
    otp = input("Enter OTP: ")
    auth.verify_otp("9876543210", "+91", otp)

# 2. Fetch Data
client = StoryTVClient(session=auth.session)
show = client.get_show_details(3413)
episodes = client.get_all_episodes(3413)

# 3. Download
downloader = Downloader(max_workers=5)
downloader.download_bulk(episodes, output_dir="./downloads", show_title=show.title)
```

## Documentation

Full documentation is available at [https://pystorytv.vrma.dev](https://pystorytv.vrma.dev).
