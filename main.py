import argparse
import csv
import json
import os
import os.path
import subprocess

from typing import Any

from beat_this.inference import File2Beats
from youtube_search import YoutubeSearch


def get_filename(id: str, artist: str, song: str) -> str:
    return (
        f"{id}-{artist}-{song}".replace(" ", "_")
        .replace("/", "_")
        .replace("?", "_")
        .lower()
    )


def download(
    output_dir: str,
    id: str,
    artist: str,
    song: str,
    *,
    force: bool = False,
    link: str | None = None,
) -> dict[str, str] | None:
    print(f"Downloading {id} - {artist} - {song}")
    filename = os.path.join(output_dir, get_filename(id, artist, song) + ".mp3")

    if os.path.exists(filename):
        if not force:
            print("File has already been downloaded.")
            return None
        os.remove(filename)

    search_result: dict[str, str] | None = None
    if link:
        url = link
    else:
        results = YoutubeSearch(
            f"{artist} {song.replace('?', '')}", max_results=1
        ).to_dict()

        if not results:
            print("ERROR: No results found for", artist, song)
            return None

        search_result = results[0]
        url = "https://www.youtube.com/watch?v=" + results[0]["id"]

    subprocess.run(
        [
            "yt-dlp",
            url,
            "-t",
            "mp3",
            "--output",
            filename,
            "--extractor-args",
            "youtube:player_client=default,-android_sdkless",
            "--cookies-from-browser",
            "firefox",
        ]
    )

    return search_result


def write_youtube_search_results(
    output_dir: str, id: str, artist: str, song: str, search_result: dict[str, Any]
) -> None:
    filename = os.path.join(output_dir, get_filename(id, artist, song) + ".txt")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(search_result, f, indent=2)


def infer_beats(
    output_dir: str, id: str, artist: str, song: str, *, force: bool = False
) -> None:
    mp3_path = os.path.join(output_dir, get_filename(id, artist, song) + ".mp3")
    beats_path = os.path.join(output_dir, get_filename(id, artist, song) + ".beats")

    if not force and os.path.exists(beats_path):
        print(f"Beats already inferred for {id} - {artist} - {song}.")
        return

    if not os.path.exists(mp3_path):
        print(
            f"ERROR: MP3 not found for {id} - {artist} - {song}, skipping beat inference."
        )
        return

    print(f"Inferring beats for {id} - {artist} - {song}")
    file2beats = File2Beats(checkpoint_path="final0", device="cpu", dbn=False)
    beats, downbeats = file2beats(mp3_path)

    downbeats_set = set(downbeats.tolist())
    with open(beats_path, "w", encoding="utf-8") as f:
        f.write("time\tis_first_in_measure\n")
        for beat in beats.tolist():
            is_first = beat in downbeats_set
            f.write(f"{beat}\t{is_first}\n")


def beats_tsv_to_csv(beats_tsv_path: str) -> str:
    """Convert a .beats TSV file to a CSV file for TiLiA import. Returns CSV path."""
    beats_csv_path = beats_tsv_path + ".csv"
    with open(beats_tsv_path, "r", encoding="utf-8") as tsv_file:
        reader = csv.reader(tsv_file, delimiter="\t")
        with open(beats_csv_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            for row in reader:
                writer.writerow(row)
    return beats_csv_path


def create_tilia_file(
    output_dir: str, id: str, artist: str, song: str, *, force: bool = False
) -> None:
    base = get_filename(id, artist, song)
    mp3_path = os.path.abspath(os.path.join(output_dir, base + ".mp3"))
    beats_tsv_path = os.path.join(output_dir, base + ".beats")
    tla_path = os.path.abspath(os.path.join(output_dir, base + ".tla"))
    script_path = os.path.abspath(os.path.join(output_dir, base + ".tilia"))

    if not force and os.path.exists(tla_path):
        print(f"TiLiA file already exists for {id} - {artist} - {song}.")
        return

    if not os.path.exists(mp3_path):
        print(
            f"ERROR: MP3 not found for {id} - {artist} - {song}, "
            "skipping TiLiA file creation."
        )
        return

    if not os.path.exists(beats_tsv_path):
        print(
            f"ERROR: Beats not found for {id} - {artist} - {song}, "
            "skipping TiLiA file creation."
        )
        return

    print(f"Creating TiLiA file for {id} - {artist} - {song}")

    beats_csv_path = os.path.abspath(beats_tsv_to_csv(beats_tsv_path))

    lines = [
        f'metadata set "title" "{song}"',
        f'metadata set "artist" "{artist}"',
        f"load-media {mp3_path}",
        "timeline add beat --name Beats --beat-pattern 1",
        f"timeline import beat --target-name Beats --file {beats_csv_path}",
        f"save {tla_path} --overwrite",
    ]

    with open(script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    subprocess.run(
        ["tilia", "-i", "cli"],
        input=f"script {script_path}\nquit\n",
        text=True,
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download songs and infer beats.")
    parser.add_argument("tsv", help="Path to songs.tsv")
    parser.add_argument(
        "--redo-download",
        action="store_true",
        help="Re-download songs even if they exist",
    )
    parser.add_argument(
        "--redo-beats",
        action="store_true",
        help="Re-infer beats even if they exist",
    )
    parser.add_argument(
        "--redo-tilia",
        action="store_true",
        help="Re-create TiLiA files even if they exist",
    )
    parser.add_argument(
        "--redo-all",
        action="store_true",
        help="Redo all steps (download, beats, tilia)",
    )
    args = parser.parse_args()

    if args.redo_all:
        args.redo_download = True
        args.redo_beats = True
        args.redo_tilia = True

    tsv_path = args.tsv
    output_dir = os.path.dirname(tsv_path)
    with open(tsv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        has_link = "link" in header
        for line in f:
            fields = line.strip().split("\t")
            id, artist, title = fields[0], fields[2], fields[3]
            link = fields[header.index("link")] if has_link else None
            try:
                search_result = download(
                    output_dir,
                    id.zfill(3),
                    artist,
                    title,
                    force=args.redo_download,
                    link=link,
                )
            except Exception:
                print("Error when searching/downloading.")
                continue

            if search_result:
                try:
                    write_youtube_search_results(
                        output_dir, id.zfill(3), artist, title, search_result
                    )
                except Exception:
                    print("Error when writing results.")

            try:
                infer_beats(
                    output_dir, id.zfill(3), artist, title, force=args.redo_beats
                )
            except Exception:
                print("Error when inferring beats.")
                continue

            try:
                create_tilia_file(
                    output_dir, id.zfill(3), artist, title, force=args.redo_tilia
                )
            except Exception:
                print("Error when creating TiLiA file.")
                continue


if __name__ == "__main__":
    main()
