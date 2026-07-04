# Models

The `pystorytv.models` module provides dataclasses representing the core data structures returned by the API.

## `Show`
Represents a TV Show / Drama.
* `id`: (int) Show ID
* `title`: (str) Title of the show
* `num_of_episodes`: (int) Total number of episodes
* `thumbnail`: (str) URL to the poster
* `metadata`: (`ShowMetadata`) Detailed information (genre, cast, description).

## `Episode`
Represents a single episode.
* `id`: (int) Internal Episode ID
* `index`: (int) The episode number (1, 2, 3...)
* `eps_title`: (str) Title of the episode
* `eps_url`: (str) The direct `.m3u8` streaming URL
* `duration`: (int) Duration in seconds
* `thumbnail`: (str) URL to the episode thumbnail

## `ExploreResults` & `SearchResults`
Wrappers for paginated API responses.
* `shows`: `list[Show]`
* `total_pages`: (int) Total pages available
* `total_elements`: (int) Total number of shows matching
