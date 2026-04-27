# journalist-helper

Command-line helper that scrapes RSS/Atom feeds and selected webpage sources, filters items relevant to Kolín, and asks OpenRouter to triage the results for a journalist.

## Usage

Set `OPENROUTER_API_KEY` in your environment, then run:

```bash
uv run python main.py
```

By default, the app loads this built-in source set:

- [České noviny - ČR](https://www.ceskenoviny.cz/sluzby/rss/cr.php)
- [Zásahy JPO](https://pkr.kr-stredocesky.cz/pkr/zasahy-jpo/feed.xml)
- [PID - mimorádnosti](https://pid.cz/feed/rss-mimoradnosti/)
- [Nehody a uzavírky - Kolín](https://www.nehody-uzavirky.cz/nehody/)
- [Uzavírky - Kolín (krátkodobé)](https://www.nehody-uzavirky.cz/uzavirky)
- [Uzavírky - Kolín (dlouhodobé)](https://www.nehody-uzavirky.cz/uzavirky-dlouhodobe)
- [Uzavírky - Kolín (plánované)](https://www.nehody-uzavirky.cz/uzavirky-planovane)
- [Nemocnice Kolín - Přehled dokumentů](https://www.nemocnicekolin.cz/dp)
- [Policie České republiky – KŘP Středočeského kraje](https://policie.gov.cz/SCRIPT/rss.aspx?nid=1314)
- [IDNES - Praha a střední Čechy](https://servis.idnes.cz/rss.aspx?c=prahah)
- [Novinky.cz - Domácí](https://api-web.novinky.cz/v1/timelines/section_5ad5a5fcc25e64000bd6e7ab?xml=rss)
- [HZS Středočeského kraje](https://hzscr.gov.cz/SCRIPT/rss.aspx?nid=17314)

The app keeps a small default relevance filter of `okres kolín` and `kolín`. Items from local operational sources such as road closures, hospital documents, police updates, and emergency services are treated as always relevant by the code.

## Output

Each run writes the triage result to `triage_result.txt` by default. Set `TRIAGE_OUTPUT_FILE` if you want a different path.

If `BOT_TOKEN` and `USER_ID` are set, the same triage output is also sent to Telegram.

## Configuration

Optional environment variables:

- `OPENROUTER_API_KEY` required for the OpenRouter triage step.
- `OPENROUTER_MODEL` overrides the default OpenRouter model.
- `BOT_TOKEN` enables Telegram alerts.
- `USER_ID` identifies the Telegram chat or user to receive alerts.
- `TRIAGE_OUTPUT_FILE` changes the file used to persist the triage output.

The app also reads environment variables from a local `.env` file.

## Notes

- When `OPENROUTER_API_KEY` is missing, the app still collects and filters sources, then records a failure message instead of stopping entirely.
- The triage summary is prepended with a per-source count block so downstream automation can see how many relevant items came from each source.

> [!NOTE]
> This project is intended for personal use only and processes public news sources plus any API or chat credentials you configure locally.

```bash
uv run python main.py
```
