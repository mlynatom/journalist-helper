# journalist-helper

Command-line helper that scrapes one or more RSS/Atom feeds, filters relevant items, and asks OpenRouter to triage the results for a journalist.

## Usage

Set `OPENROUTER_API_KEY` in your environment, then run:

```bash
uv run python main.py
```

By default (without `--feed`), the app aggregates all these feeds at once:

- https://pkr.kr-stredocesky.cz/pkr/zasahy-jpo/feed.xml
- https://pid.cz/feed/rss-mimoradnosti/
- https://www.ceskenoviny.cz/sluzby/rss/cr.php

Use custom feeds (can be repeated):

```bash
uv run python main.py \
	--feed https://pkr.kr-stredocesky.cz/pkr/zasahy-jpo/feed.xml \
	--feed https://pid.cz/feed/rss-mimoradnosti/ \
	--feed https://www.ceskenoviny.cz/sluzby/rss/cr.php
```

Use custom relevance keywords (can be repeated):

```bash
uv run python main.py --keyword "okres Kolín" --keyword "Kolín"
```

Optional environment variables:

- `OPENROUTER_MODEL` to override the default OpenRouter model.
- `RSS_FEED_URLS` comma or newline separated feed URLs.
- `RSS_FILTER_KEYWORDS` comma or newline separated filter keywords.