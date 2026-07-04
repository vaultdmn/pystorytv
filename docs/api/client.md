# API Client

The `StoryTVClient` class handles all data retrieval from the StoryTV endpoints.

```python
from pystorytv import AuthManager, StoryTVClient

auth = AuthManager()
client = StoryTVClient(session=auth.session)
```

## Methods

### `explore(page: int = 0, size: int = 20) -> ExploreResults`
Returns the latest shows in the currently selected language.

```python
results = client.explore(page=0, size=50)
for show in results.shows:
    print(show.title)
```

### `search(query: str, page: int = 0, size: int = 20) -> SearchResults`
Searches the entire catalog for a specific query.

### `get_show_details(show_id: int) -> ShowInfo`
Gets detailed metadata for a show, including total episode count, genre, description, and cast.

### `get_all_episode_metadata(show_id: int) -> list[Episode]`
Automatically handles pagination to fetch **every single episode** for a given show. This is highly recommended over manual pagination.

```python
episodes = client.get_all_episode_metadata(3413)
print(f"Total episodes: {len(episodes)}")
print(f"First Episode URL: {episodes[0].eps_url}")
```

### `select_language(lang_id: int) -> None`
Changes the active session language.
* `1` = Hindi
* `2` = Tamil
* `3` = Telugu
* `4` = Malayalam
* ...and so on.
