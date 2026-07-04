"""Configuration and session management for StoryTV."""
from __future__ import annotations

import json
import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "storytv"
APP_AUTHOR = "storytv"

# --- Paths ------------------------------------------------------------------

def _data_dir() -> Path:
    p = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    p.mkdir(parents=True, exist_ok=True)
    return p


def session_file() -> Path:
    return _data_dir() / "session.json"


def config_file() -> Path:
    return _data_dir() / "config.json"


# --- Session ----------------------------------------------------------------

class Session:
    """Holds the authenticated user session (JWT + refresh token)."""

    def __init__(
        self,
        jwt: str,
        rft: str,
        user_id: int,
        session_id: int,
        mobile: str,
        sub_stat: str,
    ) -> None:
        self.jwt = jwt
        self.rft = rft
        self.user_id = user_id
        self.session_id = session_id
        self.mobile = mobile
        self.sub_stat = sub_stat  # "0"=free "1"=trial "2"=premium

    # --- Serialisation ------------------------------------------------------

    def save(self) -> None:
        f = session_file()
        f.write_text(
            json.dumps(
                {
                    "jwt": self.jwt,
                    "rft": self.rft,
                    "user_id": self.user_id,
                    "session_id": self.session_id,
                    "mobile": self.mobile,
                    "sub_stat": self.sub_stat,
                }
            )
        )

    @classmethod
    def load(cls) -> "Session | None":
        f = session_file()
        if not f.exists():
            return None
        try:
            d = json.loads(f.read_text())
            return cls(**d)
        except Exception:
            return None

    @classmethod
    def clear(cls) -> None:
        f = session_file()
        if f.exists():
            f.unlink()

    @property
    def is_premium(self) -> bool:
        return self.sub_stat in ("1", "2")


# --- App Config -------------------------------------------------------------

class Config:
    """Persistent user preferences."""

    def __init__(self) -> None:
        self.download_dir: str = str(Path.home() / "Downloads" / "StoryTV")
        self.preferred_quality: str = "best"
        self.lang_id: int = 2  # Hindi default

    def save(self) -> None:
        config_file().write_text(
            json.dumps(
                {
                    "download_dir": self.download_dir,
                    "preferred_quality": self.preferred_quality,
                    "lang_id": self.lang_id,
                }
            )
        )

    @classmethod
    def load(cls) -> "Config":
        c = cls()
        f = config_file()
        if f.exists():
            try:
                d = json.loads(f.read_text())
                c.download_dir = d.get("download_dir", c.download_dir)
                c.preferred_quality = d.get("preferred_quality", c.preferred_quality)
                c.lang_id = d.get("lang_id", c.lang_id)
            except Exception:
                pass
        return c
