# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python CLI tool that bulk-downloads music from YouTube. Reads song metadata (ID, year, title, artist) from TSV files, searches YouTube via `youtube-search`, and downloads audio as MP3 using `yt-dlp`. Outputs both the audio file and a JSON metadata file per song.

## Commands

```bash
# Setup
uv sync                    # Install dependencies
uv run pre-commit install  # Install git hooks

# Run (yt-dlp must be installed separately and available on $PATH)
python main.py <dataset>/songs.tsv                # Download songs into <dataset>/
python main.py <dataset>/songs.tsv --redo-download # Force re-download existing songs
python main.py <dataset>/songs.tsv --redo-beats   # Force re-infer beats

# Lint, Format & Type Check
uv run ruff check --fix .  # Lint (with auto-fix)
uv run ruff format .       # Format
uv run mypy main.py        # Type check
uv run pre-commit run --all-files  # Run all pre-commit hooks
```

No test suite is configured.

## Architecture

Single-file application (`main.py`, ~67 lines) with four functions:

- **`get_filename(id, artist, song)`** — Builds sanitized, lowercase filename from metadata
- **`download(output_dir, id, artist, song)`** — Skips existing files, searches YouTube, runs `yt-dlp` subprocess with Firefox cookies, returns search result metadata
- **`write_youtube_search_results(output_dir, id, artist, song, search_result)`** — Writes YouTube search metadata as JSON to `.txt` file
- **`main()`** — Reads TSV from CLI arg, derives output dir from TSV path, orchestrates download + metadata writing with per-song error handling

## Data Format

TSV input (`songs.tsv`): `id\tyear\ttitle\tartist`

Output per song:
- `{id}-{artist}-{title}.mp3` — audio
- `{id}-{artist}-{title}.txt` — YouTube search result JSON

## Tech Stack

- Python 3.12+, managed with `uv`
- `youtube-search` for YouTube search
- `yt-dlp` for audio download (uses Firefox cookies for auth)