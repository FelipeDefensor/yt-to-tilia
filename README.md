# yt-to-tilia

CLI tool that bulk-downloads music from YouTube and produces [TiLiA](https://tilia-ad98d.web.app/) project files with beat annotations.

## What it does

For each song in a TSV file, the tool:

1. Searches YouTube (or uses a provided URL) and downloads the audio as MP3 via `yt-dlp`
2. Infers beat positions using [beat-this](https://github.com/CPJKU/beat_this)
3. Creates a TiLiA `.tla` project file pre-loaded with the audio and beat timeline

## Prerequisites

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed and on your `PATH`
- Firefox logged in to YouTube (used for authentication cookies)
- Python 3.12+ with [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## Usage

### Batch mode (TSV)

```bash
python main.py <dataset>/songs.tsv
```

Output directory is derived from the TSV path — all files are written next to it.

### One-off mode

```bash
# Direct URL
python main.py --link "https://www.youtube.com/watch?v=..." [--artist X] [--title Y] [--id N] [--output-dir DIR]

# YouTube search
python main.py --search --title "Hyrule Field Main Theme" [--artist X] [--id N] [--output-dir DIR]
```

`--artist`, `--title`, and `--id` are optional (default ID: `001`). Missing artist/title are derived from the YouTube result. Output defaults to the current directory.

### Common flags

| Flag | Description |
|---|---|
| `--redo-download` | Re-download songs even if the MP3 already exists |
| `--redo-beats` | Re-infer beats even if the `.beats` file already exists |
| `--redo-tilia` | Re-create TiLiA files even if the `.tla` already exists |
| `--redo-all` | Shorthand for all three `--redo-*` flags |

## Input format

Tab-separated file with a header row:

```
id	year	artist	title
1	1977	Fleetwood Mac	Dreams
2	1969	The Beatles	Come Together
```

An optional `link` column can supply a direct YouTube URL, skipping the search step.

## Output

Per song:

| File | Description |
|---|---|
| `{id}-{artist}-{title}.mp3` | Downloaded audio |
| `{id}-{artist}-{title}.txt` | YouTube search result metadata (JSON) |
| `{id}-{artist}-{title}.beats` | Inferred beat times (TSV) |
| `{id}-{artist}-{title}.tla` | TiLiA project file |
