"""Data models for StoryTV API responses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Auth / User
# ---------------------------------------------------------------------------

@dataclass
class AuthResponse:
    user_id: int
    jwt: str
    rft: str
    session_id: int
    sub_stat: str
    mobile: str
    is_new_user: bool = False


# ---------------------------------------------------------------------------
# Show / Content
# ---------------------------------------------------------------------------

@dataclass
class ShowMetadata:
    genre: str = ""
    tags: list[str] = field(default_factory=list)
    is_original: bool = False


@dataclass
class WatchInfo:
    total_episodes: Optional[str] = None
    watched_episodes: Optional[str] = None
    view_count: Optional[str] = None


@dataclass
class Show:
    id: str
    title: str
    image_url: str
    metadata: ShowMetadata = field(default_factory=ShowMetadata)
    watch_info: WatchInfo = field(default_factory=WatchInfo)
    num_of_episodes: Optional[int] = None
    ep_url: Optional[str] = None  # latest/first episode m3u8

    @classmethod
    def from_dict(cls, d: dict) -> "Show":
        meta_d = d.get("metadata") or {}
        wi_d = d.get("watchInfo") or {}
        return cls(
            id=str(d["id"]),
            title=d["title"],
            image_url=d.get("imageUrl", ""),
            metadata=ShowMetadata(
                genre=meta_d.get("genre", ""),
                tags=meta_d.get("tags") or [],
                is_original=meta_d.get("isOriginal", False),
            ),
            watch_info=WatchInfo(
                total_episodes=wi_d.get("totalEpisodes"),
                watched_episodes=wi_d.get("watchedEpisodes"),
                view_count=wi_d.get("vc"),
            ),
            num_of_episodes=d.get("numOfEpisodes"),
            ep_url=d.get("epUrl"),
        )


# ---------------------------------------------------------------------------
# Episode
# ---------------------------------------------------------------------------

@dataclass
class Episode:
    index: int
    content_id: str
    eps_url: str
    eps_title: str
    sub_txt: str        # e.g. "3/51"
    thumb: str
    like_count: str
    liked: bool
    is_watched: Optional[bool] = None
    lock: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "Episode":
        return cls(
            index=d["index"],
            content_id=str(d.get("contentId", d.get("index", ""))),
            eps_url=d.get("epsUrl", ""),
            eps_title=d.get("epsTitle", f"Episode {d['index']}"),
            sub_txt=d.get("subTxt", ""),
            thumb=d.get("thumb", ""),
            like_count=d.get("lkCnt", ""),
            liked=d.get("lkd", False),
            is_watched=d.get("isWtch"),
            lock=d.get("lock", False),
        )


# ---------------------------------------------------------------------------
# Episode List (from /episode/list/{show_id})
# ---------------------------------------------------------------------------

@dataclass
class EpisodeListInfo:
    """Lightweight episode list (no URLs – just indices/lock status)."""
    show_title: str
    show_id: str
    genre: str
    ep_count: int
    bookmarked: bool
    bookmark_count: str
    last_watched: int
    next_show_id: Optional[str]
    next_show_title: Optional[str]
    episodes: list[EpisodeBrief] = field(default_factory=list)
    page_size: int = 25
    page_headers: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "EpisodeListInfo":
        return cls(
            show_title=d.get("showTitle", ""),
            show_id=str(d.get("showId", "")),
            genre=d.get("genre", ""),
            ep_count=d.get("epCount", 0),
            bookmarked=d.get("bMark", False),
            bookmark_count=d.get("bMarkCnt", ""),
            last_watched=d.get("lstWtch", 0),
            next_show_id=d.get("nextShowId"),
            next_show_title=d.get("nextShowTitle"),
            episodes=[EpisodeBrief.from_dict(e) for e in (d.get("data") or [])],
            page_size=d.get("pageSize", 25),
            page_headers=d.get("pageHeaders") or [],
        )


@dataclass
class EpisodeBrief:
    index: int
    ep_title: str
    lock: bool
    type: str
    is_watched: Optional[bool] = None

    @classmethod
    def from_dict(cls, d: dict) -> "EpisodeBrief":
        return cls(
            index=d["index"],
            ep_title=d.get("epTitle", str(d["index"])),
            lock=d.get("lock", False),
            type=d.get("type", "EPISODE"),
            is_watched=d.get("isWtch"),
        )


# ---------------------------------------------------------------------------
# Homepage / Feed
# ---------------------------------------------------------------------------

@dataclass
class HomepageSection:
    id: str
    layout: str
    text: Optional[str] = None
    action_text: Optional[str] = None
    has_bg_gradient: bool = False
    btn_override: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "HomepageSection":
        return cls(
            id=str(d["id"]),
            layout=d.get("lyt", ""),
            text=d.get("text"),
            action_text=d.get("acttxt"),
            has_bg_gradient=d.get("sBgG", False),
            btn_override=d.get("btnover"),
        )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    shows: list[Show]
    total_elements: int
    total_pages: int
    page: int
    page_size: int
    is_last: bool

    @classmethod
    def from_dict(cls, d: dict) -> "SearchResult":
        content = [Show.from_dict(s) for s in (d.get("content") or [])]
        return cls(
            shows=content,
            total_elements=d.get("totalElements", len(content)),
            total_pages=d.get("totalPages", 1),
            page=d.get("number", 0),
            page_size=d.get("size", 20),
            is_last=d.get("last", True),
        )
