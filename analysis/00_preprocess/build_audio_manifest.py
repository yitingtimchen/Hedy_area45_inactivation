from __future__ import annotations

from pathlib import Path
import struct

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "data" / "raw" / "boris"
VIDEOS_DIR = ROOT / "data" / "raw" / "videos_720p"
OUTPUTS_DIR = ROOT / "data" / "derived" / "audio"


def read_box_header(handle, end_pos: int):
    pos = handle.tell()
    if pos + 8 > end_pos:
        return None
    header = handle.read(8)
    if len(header) < 8:
        return None
    size, box_type = struct.unpack(">I4s", header)
    header_size = 8
    if size == 1:
        ext = handle.read(8)
        if len(ext) < 8:
            return None
        size = struct.unpack(">Q", ext)[0]
        header_size = 16
    elif size == 0:
        size = end_pos - pos
    return pos, size, box_type.decode("latin1"), header_size


def find_child_box(handle, start_pos: int, size: int, wanted: str):
    end_pos = start_pos + size
    handle.seek(start_pos + 8)
    while handle.tell() < end_pos:
        item = read_box_header(handle, end_pos)
        if item is None:
            return None
        pos, box_size, box_type, header_size = item
        if box_type == wanted:
            return pos, box_size, header_size
        handle.seek(pos + box_size)
    return None


def has_audio_track(path: Path) -> bool:
    with path.open("rb") as handle:
        file_end = path.stat().st_size
        moov = None
        while handle.tell() < file_end:
            item = read_box_header(handle, file_end)
            if item is None:
                break
            pos, size, box_type, _ = item
            if box_type == "moov":
                moov = (pos, size)
                break
            handle.seek(pos + size)

        if moov is None:
            return False

        moov_pos, moov_size = moov
        moov_end = moov_pos + moov_size
        handle.seek(moov_pos + 8)
        while handle.tell() < moov_end:
            item = read_box_header(handle, moov_end)
            if item is None:
                break
            pos, size, box_type, _ = item
            if box_type != "trak":
                handle.seek(pos + size)
                continue

            mdia = find_child_box(handle, pos, size, "mdia")
            if not mdia:
                handle.seek(pos + size)
                continue
            mdia_pos, mdia_size, _ = mdia
            hdlr = find_child_box(handle, mdia_pos, mdia_size, "hdlr")
            if not hdlr:
                handle.seek(pos + size)
                continue
            hdlr_pos, hdlr_size, hdlr_header = hdlr
            handle.seek(hdlr_pos + hdlr_header)
            data = handle.read(hdlr_size - hdlr_header)
            if len(data) >= 12:
                handler_type = data[8:12].decode("latin1", errors="ignore")
                if handler_type == "soun":
                    return True
            handle.seek(pos + size)
    return False


def build_manifest() -> pd.DataFrame:
    rows = []
    for table_path in sorted(TABLES_DIR.glob("*.pkl")):
        session_id = table_path.stem
        table = pd.read_pickle(table_path)
        source_parts = str(table["Source"].dropna().iloc[0]).split("|")
        duration_parts = str(table["Media duration (s)"].dropna().iloc[0]).split("|")

        media_rows = []
        for source_text, duration_text in zip(source_parts, duration_parts):
            source_path = Path(source_text.split(":", 1)[1])
            video_path = source_path
            candidate = VIDEOS_DIR / video_path.name.replace("_synced.mp4", "_synced_720p.mp4")
            if candidate.exists() and (not video_path.exists() or video_path.parent.name != "videos_720p"):
                video_path = candidate
            if not video_path.is_absolute():
                video_path = (ROOT / video_path).resolve()
            media_rows.append(
                {
                    "file_name": video_path.name,
                    "file_path": str(video_path),
                    "duration_s": float(duration_text),
                    "has_audio": has_audio_track(video_path),
                }
            )

        ordered = sorted(media_rows, key=lambda row: row["duration_s"], reverse=True)
        selected = None
        reason = "no_audio_in_longest_or_second"
        if ordered[0]["has_audio"]:
            selected = ordered[0]
            reason = "longest_has_audio"
        elif ordered[1]["has_audio"]:
            selected = ordered[1]
            reason = "fallback_second_longest"

        rows.append(
            {
                "session_id": session_id,
                "longest_file": ordered[0]["file_name"],
                "longest_path": ordered[0]["file_path"],
                "longest_duration_s": ordered[0]["duration_s"],
                "longest_has_audio": ordered[0]["has_audio"],
                "second_file": ordered[1]["file_name"],
                "second_path": ordered[1]["file_path"],
                "second_duration_s": ordered[1]["duration_s"],
                "second_has_audio": ordered[1]["has_audio"],
                "shortest_file": ordered[2]["file_name"],
                "shortest_path": ordered[2]["file_path"],
                "shortest_duration_s": ordered[2]["duration_s"],
                "shortest_has_audio": ordered[2]["has_audio"],
                "selected_audio_file": None if selected is None else selected["file_name"],
                "selected_audio_path": None if selected is None else selected["file_path"],
                "selected_audio_duration_s": None if selected is None else selected["duration_s"],
                "selection_reason": reason,
            }
        )

    return pd.DataFrame(rows).sort_values("session_id").reset_index(drop=True)


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    manifest.to_csv(OUTPUTS_DIR / "blinded_audio_manifest.csv", index=False)


if __name__ == "__main__":
    main()
