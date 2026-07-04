"""StoryTV API client — wraps all REST endpoints discovered via network recon."""
from __future__ import annotations

import time
import uuid
from typing import Any, Optional

import httpx

from pystorytv.config import Session
from pystorytv.models import (
    AuthResponse,
    Episode,
    EpisodeListInfo,
    HomepageSection,
    SearchResult,
    Show,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://api.storytv.asia"
CDN_URL = "https://cdn.storytv.asia"

# Spoof the same Android device headers the app uses
_DEVICE_ID = "72f8b873c1118da2"
_OS = "Android 9 (API 28)"
_MODEL = "A5010"
_BRAND = "OnePlus"
_APP_VERSION = "60"
_PLATFORM = "0"

HEADERS_BASE = {
    "model_name": _MODEL,
    "brand": _BRAND,
    "manf": _BRAND,
    "appVersion": _APP_VERSION,
    "platform": _PLATFORM,
    "deviceId": _DEVICE_ID,
    "os": _OS,
    "network_type": "WIFI",
    "Accept": "application/json",
    "User-Agent": "ktor-client",
    "Content-Type": "application/json",
}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class StoryTVError(Exception):
    """Generic API error."""


class AuthError(StoryTVError):
    """Authentication failed."""


class APIError(StoryTVError):
    """Non-200 API response."""
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class StoryTVClient:
    """
    Synchronous HTTP client wrapping all StoryTV REST APIs.

    Usage::

        client = StoryTVClient(session)
        results = client.search("hacker king")
        for show in results.shows:
            print(show.title)
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._http = httpx.Client(
            base_url=BASE_URL,
            headers=self._build_headers(),
            timeout=20,
            follow_redirects=True,
            verify=False,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        h = {**HEADERS_BASE, "ts": str(int(time.time()))}
        if self._session:
            h["Authorization"] = f"Bearer {self._session.jwt}"
        else:
            h["Authorization"] = "Bearer"
        return h

    def _refresh_ts(self) -> None:
        """Refresh timestamp header before each request."""
        self._http.headers["ts"] = str(int(time.time()))
        if self._session:
            self._http.headers["Authorization"] = f"Bearer {self._session.jwt}"

    def _get(self, path: str, _extra_headers: Optional[dict] = None, **kwargs) -> Any:
        self._refresh_ts()
        headers = self._http.headers.copy()
        if _extra_headers:
            headers.update(_extra_headers)

        r = self._http.get(path, params=kwargs, headers=headers)
        r.raise_for_status()
        j = r.json()
        if j.get("code", 200) not in (200, 201):
            raise APIError(j["code"], j.get("message", "Unknown error"))
        return j.get("data", j)

    def _post(self, path: str, json_body: Any = None) -> dict:
        self._refresh_ts()
        r = self._http.post(path, json=json_body)
        r.raise_for_status()
        j = r.json()
        if j.get("code", 200) not in (200, 201):
            raise APIError(j["code"], j.get("message", "Unknown error"))
        return j.get("data", j)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def get_languages(self) -> list[dict]:
        """Fetch available languages."""
        d = self._get("/userservice/v1/languages")
        return d.get("languages", [])

    def select_language(self, lang_id: str) -> None:
        """Update the user's language selection."""
        self._post("/userservice/v1/language/select", json_body={"langId": int(lang_id)})

    def verify_otpless(self, token: str, id_token: str) -> AuthResponse:
        """
        Exchange an OTPLess token+id_token pair for a StoryTV JWT.

        The OTP flow itself (phone → OTP → OTPLess token) must be done
        externally via the /auth module (or manually).
        """
        body = {"token": token, "id_token": id_token}
        raw = self._http.post(
            "/userservice/v1/otpless/verify",
            json=body,
            headers={**HEADERS_BASE, "Authorization": "Bearer", "ts": str(int(time.time()))},
        )
        raw.raise_for_status()
        j = raw.json()
        if j.get("code", 200) not in (200, 201):
            raise AuthError(j.get("message", "OTPLess verify failed"))
        d = j["data"]
        return AuthResponse(
            user_id=d["id"],
            jwt=d["jwt"],
            rft=d["rft"],
            session_id=d["session"],
            sub_stat=d.get("subStat", "0"),
            mobile=d.get("mob", ""),
            is_new_user=not d.get("nwusr", True),
        )

    def get_subscription_state(self) -> dict:
        return self._get("/userservice/v1/profile/subscription/state")

    def get_languages(self) -> list[dict]:
        d = self._get("/userservice/v1/languages")
        return d.get("languages", [])

    # ------------------------------------------------------------------
    # Feed / Homepage
    # ------------------------------------------------------------------

    def get_homepage_sections(self) -> list[HomepageSection]:
        d = self._get("/feedservice/v1/homepage/struct")
        return [HomepageSection.from_dict(s) for s in (d.get("sections") or [])]

    def get_continue_watching(self) -> Optional[Show]:
        try:
            d = self._get("/feedservice/v1/show/cw")
            return Show.from_dict(d)
        except Exception:
            return None

    def get_section_shows(
        self, section_id: str | int, page: int = 0, size: int = 15
    ) -> list[Show]:
        d = self._get(f"/feedservice/v1/shows/{section_id}", page=page, size=size)
        return [Show.from_dict(s) for s in (d.get("content") or [])]

    def get_explore_shows(
        self, page: int = 0, size: int = 10, int_count: int = 0
    ) -> list[Show]:
        """Explore/discover feed (vertical scroll in the app)."""
        d = self._get(
            "/feedservice/v2/explore/shows",
            page=page,
            size=size,
            intCount=int_count,
        )
        raw_content = d.get("content") or []
        shows: list[Show] = []
        for item in raw_content:
            show_d = item.get("data", {}).get("showInfo")
            if show_d:
                shows.append(Show.from_dict(show_d))
        return shows

    def get_suggested_shows(self, show_id: str | int, shuffle: bool = False) -> list[Show]:
        d = self._get(
            "/feedservice/v1/suggested/shows",
            showId=show_id,
            shuffle=str(shuffle).lower(),
        )
        return [Show.from_dict(s) for s in (d.get("content") or [])]

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, page: int = 0, size: int = 20) -> SearchResult:
        import urllib.parse
        encoded = urllib.parse.quote(query)
        d = self._get(f"/searchservice/v1/search/{encoded}", page=page, size=size)
        return SearchResult.from_dict(d)

    def explore(self, page: int = 0, size: int = 20) -> SearchResult:
        d = self._get("/feedservice/v2/explore/shows", page=page, size=size, intCount=0)
        # explore/shows returns a slightly different format (list of {type, data: {showInfo: ...}}),
        # but we can map it to SearchResult.
        shows = []
        seen_ids = set()
        for item in d.get("content", []):
            info = item.get("data", {}).get("showInfo")
            if info:
                show_id = str(info.get("id"))
                if show_id not in seen_ids:
                    seen_ids.add(show_id)
                    shows.append(Show.from_dict(info))
        
        return SearchResult(
            shows=shows,
            page=d.get("pageable", {}).get("pageNumber", 0),
            page_size=size,
            is_last=d.get("last", True),
            total_pages=d.get("totalPages", 1),
            total_elements=d.get("totalElements", len(shows)),
        )

    # ------------------------------------------------------------------
    # Episodes
    # ------------------------------------------------------------------

    def get_episode_list(self, show_id: str | int) -> EpisodeListInfo:
        """
        Returns lightweight episode list (index, lock, watch status).
        No stream URLs here — use get_episode_metadata for those.
        """
        d = self._get(f"/feedservice/v1/episode/list/{show_id}")
        return EpisodeListInfo.from_dict(d)

    def get_episode_metadata(
        self,
        show_id: str | int,
        cursor: Optional[int] = None,
        direction: str = "NEXT",
    ) -> list[Episode]:
        """
        Returns up to 5 episodes with signed m3u8 stream URLs.
        Use cursor + direction to page through (cursor = last index seen).
        """
        params: dict[str, Any] = {}
        if cursor is not None:
            params["cursor"] = cursor
            params["dir"] = direction
        d = self._get(f"/feedservice/v1/episode/metadata/{show_id}", **params)
        return [Episode.from_dict(e) for e in (d.get("content") or [])]

    def get_all_episode_metadata(self, show_id: str | int) -> list[Episode]:
        """
        Convenience: fetches ALL episode metadata for a show by paging
        through /episode/metadata/{show_id} until exhausted.
        Returns list sorted by episode index.
        """
        episodes: list[Episode] = []
        cursor: Optional[int] = None

        while True:
            batch = self.get_episode_metadata(show_id, cursor=cursor)
            if not batch:
                break
            episodes.extend(batch)
            last_index = batch[-1].index
            # Stop if cursor didn't advance (safety against infinite loops)
            if cursor is not None and last_index <= cursor:
                break
            cursor = last_index

        # Deduplicate & sort
        seen: set[int] = set()
        result: list[Episode] = []
        for ep in sorted(episodes, key=lambda e: e.index):
            if ep.index not in seen:
                seen.add(ep.index)
                result.append(ep)
        return result

    # ------------------------------------------------------------------
    # My List (Bookmarks / History)
    # ------------------------------------------------------------------

    def get_my_list_struct(self) -> list[dict]:
        d = self._get("/feedservice/v1/mylist/struct")
        return d.get("sections") or []

    def add_to_my_list(self, show_id: str | int, add_show: bool = True) -> dict:
        return self._post(
            "/feedservice/v1/mylist/add",
            {"shId": str(show_id), "adShw": add_show},
        )

    def remove_from_my_list(self, show_id: str | int, section_id: str | int) -> dict:
        return self._post(
            "/feedservice/v1/mylist/delete",
            {"shId": str(show_id), "secId": str(section_id)},
        )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def get_share_info(self, show_id: str | int) -> dict:
        return self._get(f"/feedservice/v1/shows/share/{show_id}")

    def get_category_details(self) -> list[dict]:
        d = self._get("/feedservice/v1/category/details")
        return d.get("categories") or []

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "StoryTVClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
