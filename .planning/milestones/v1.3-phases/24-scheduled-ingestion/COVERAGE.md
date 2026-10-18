# API Coverage — YouTube (Atom feed surface)

> Full coverage by default. Opt-outs are explicit, reasoned decisions.
> Phase 24 integrates one external surface: the **key-free public YouTube Atom feed**
> (`https://www.youtube.com/feeds/videos.xml`). The key-based YouTube Data API v3 is
> explicitly rejected by ROADMAP § Phase 24 and `24-CONTEXT.md` (Out of scope), so its
> capabilities are recorded here as reasoned opt-outs rather than silently absent.

| capability | decision | reason |
|---|---|---|
| `feed_listing_channel` — `?channel_id=UC…` | INTEGRATE | ING-02 primary path; canonical `UC…` ids only (Phase 23 validates them) |
| `feed_listing_playlist` — `?playlist_id=PL…` | INTEGRATE | Same adapter, `PL…` ids already stored by Phase 23 |
| `entry_parse` — `yt:videoId` + `published` | INTEGRATE | D-24: bare video id + tz-aware timestamp, nothing else |
| `feed_error_taxonomy` — non-200 / broken XML / oversize | INTEGRATE | D-11, D-25, D-26: source-level failure, one stderr line, continue |
| `feed_pagination` / `continuation` | OPT-OUT | Atom feed exposes the ~15 most recent entries with no pagination token; the window plus the per-source high-water mark (D-06) covers the scheduled cadence |
| `data_api_search` | OPT-OUT | Explicitly rejected by ROADMAP Notes; key-based contour conflicts with ADR-0002 and success criterion 5 (zero new runtime packages) |
| `data_api_videos_list` (duration, statistics, tags) | OPT-OUT | Not needed for drafts; captions and metadata already come from the existing `ingest` pipeline |
| `handle_resolution` (`@handle` → `UC…`) | OPT-OUT | Out of scope in ROADMAP and `24-CONTEXT.md`; admins paste canonical ids |
| `client_library` (`google-api-python-client` / `yt-dlp` / `feedparser`) | OPT-OUT | Success criterion 5: zero new runtime Python packages; stdlib `xml.etree.ElementTree` + injected `httpx` client only |
| `ingest_pipeline` (captions → LLM → persist) | INTEGRATE | Reused via `run_ingest_pipeline` with `on_stage=None` (D-03); not re-implemented |
| `publish` / `send` | OPT-OUT | Forbidden on this path by design (PITFALL 23); proven by the ING-07 guard test |
| `run_history_store` | OPT-OUT | D-10: journald + `systemctl --failed` instead of an `ingestion_runs` table |
