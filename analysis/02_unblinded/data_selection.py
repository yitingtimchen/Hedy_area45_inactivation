from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import re
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd


PARENT_01 = Path(__file__).resolve().parents[1] / "01_blinded"
if str(PARENT_01) not in sys.path:
    sys.path.insert(0, str(PARENT_01))

from compute_quiet_mask_sensitivity import compute_smoothed_loud_mask, reciprocity_score  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
BLINDED_TABLES = ROOT / "results" / "blinded" / "tables"
DERIVED_AUDIO = ROOT / "data" / "derived" / "audio" / "blinded_audio_features_1s_labeled.csv"
KEY_PATH = ROOT / "data" / "raw" / "session_key" / "Sessions name encoding.xlsx"
VET_ENTRY_SESSION_ID = "596273"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

LOUD_STRESS_SOCIAL = {"Aggressive vocal", "Enlist/Recruit", "Cage-shake display"}
LOUD_STRESS_ACTIVITY = {"Chew non-food", "Object manipulate", "Pace"}


def load_xlsx_sheet_rows(path: Path) -> pd.DataFrame:
    with ZipFile(path) as zf:
        shared_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        shared = [
            "".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
            for si in shared_root.findall("a:si", NS)
        ]
        sheet_root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))

    rows: list[dict[str, str]] = []
    for row in sheet_root.findall(".//a:sheetData/a:row", NS):
        cells: dict[str, str] = {}
        for cell in row.findall("a:c", NS):
            ref = cell.get("r", "")
            col = re.sub(r"\d+", "", ref)
            cell_type = cell.get("t")
            value_node = cell.find("a:v", NS)
            value = ""
            if value_node is not None:
                value = value_node.text or ""
                if cell_type == "s":
                    value = shared[int(value)]
            cells[col] = value
        if cells.get("A") and cells.get("B") and cells.get("D"):
            rows.append(cells)
    return pd.DataFrame(rows)


def load_unblinding_map() -> pd.DataFrame:
    raw = load_xlsx_sheet_rows(KEY_PATH)
    mapping = raw.assign(
        session_id=raw["D"].str.extract(r"(\d+)_"),
        original_name=raw["A"],
        condition=raw["B"],
        date_str=raw["A"].str.extract(r"^(\d{8})_"),
    )
    mapping["date"] = pd.to_datetime(mapping["date_str"], format="%Y%m%d")
    mapping["condition"] = mapping["condition"].replace({"Saline": "vehicle", "Inactivation": "DCZ"})
    session_map = (
        mapping.groupby("session_id", as_index=False)
        .agg(original_name=("original_name", "first"), condition=("condition", "first"), date=("date", "first"))
        .sort_values("date")
        .reset_index(drop=True)
    )
    session_map["session_index"] = np.arange(1, len(session_map) + 1)
    return session_map


def _audio_selection_summaries() -> pd.DataFrame:
    audio = pd.read_csv(DERIVED_AUDIO, dtype={"session_id": str})
    rows: list[dict[str, object]] = []
    for session_id, group in audio.groupby("session_id", sort=False):
        ordered = group.sort_values("bin_start_s").reset_index(drop=True)
        loud_mask, _, _ = compute_smoothed_loud_mask(ordered)
        quiet_mask = ~loud_mask
        selections = {
            "full": np.ones(len(ordered), dtype=bool),
            "exclude_smoothed_loud_epochs": quiet_mask,
            "include_smoothed_loud_epochs_only": loud_mask,
        }
        row: dict[str, object] = {"session_id": str(session_id)}
        for selection_name, mask in selections.items():
            sub = ordered.loc[mask].copy()
            duration_s = float(sub["bin_duration_s"].sum())
            forage_s = float(sub["activity_state"].eq("Forage/Search").sum())
            travel_s = float(sub["activity_state"].eq("Travel").sum())
            rest_s = float(sub["activity_state"].eq("Rest/Stationary").sum())
            scratch_s = float(sub["activity_state"].eq("Scratch").sum())
            vigilant_s = float(sub["attention_state"].eq("Vigilant/Scan").sum())
            outside_attention_s = float(sub["attention_state"].eq("Attention to outside agents").sum())
            hiccups_s = float(sub["atypical_state"].eq("Hiccups").sum())
            stress_s = float(
                sub["social_state"].isin(LOUD_STRESS_SOCIAL).sum()
                + sub["activity_state"].isin(LOUD_STRESS_ACTIVITY).sum()
            )
            row[f"{selection_name}_duration_s"] = duration_s
            row[f"forage_search_duration_s__{selection_name}"] = forage_s
            row[f"forage_search_pct__{selection_name}"] = 100.0 * forage_s / duration_s if duration_s > 0 else np.nan
            row[f"travel_duration_s__{selection_name}"] = travel_s
            row[f"travel_pct__{selection_name}"] = 100.0 * travel_s / duration_s if duration_s > 0 else np.nan
            row[f"rest_stationary_duration_s__{selection_name}"] = rest_s
            row[f"rest_stationary_pct__{selection_name}"] = 100.0 * rest_s / duration_s if duration_s > 0 else np.nan
            row[f"scratch_duration_s__{selection_name}"] = scratch_s
            row[f"scratch_pct__{selection_name}"] = 100.0 * scratch_s / duration_s if duration_s > 0 else np.nan
            row[f"vigilant_scan_duration_s__{selection_name}"] = vigilant_s
            row[f"vigilant_scan_pct__{selection_name}"] = 100.0 * vigilant_s / duration_s if duration_s > 0 else np.nan
            row[f"attention_outside_duration_s__{selection_name}"] = outside_attention_s
            row[f"attention_outside_pct__{selection_name}"] = 100.0 * outside_attention_s / duration_s if duration_s > 0 else np.nan
            row[f"hiccups_duration_s__{selection_name}"] = hiccups_s
            row[f"hiccups_pct__{selection_name}"] = 100.0 * hiccups_s / duration_s if duration_s > 0 else np.nan
            row[f"loud_stress_composite_duration_s__{selection_name}"] = stress_s
            row[f"loud_stress_composite_pct__{selection_name}"] = 100.0 * stress_s / duration_s if duration_s > 0 else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def _build_base_table() -> pd.DataFrame:
    session_map = load_unblinding_map()
    decision = pd.read_csv(BLINDED_TABLES / "blinded_decision_table.csv", dtype={"session_id": str})
    session_summary = pd.read_csv(BLINDED_TABLES / "blinded_session_summary.csv", dtype={"session_id": str})
    social = pd.read_csv(BLINDED_TABLES / "blinded_social_nonprecedence_metrics_by_session.csv", dtype={"session_id": str})
    audio_summary = _audio_selection_summaries()

    base = (
        session_map
        .merge(decision, on="session_id", how="inner", suffixes=("", "_decision"))
        .merge(
            session_summary[
                [
                    "session_id",
                    "groom_give_resolved_duration_s",
                    "groom_receive_resolved_duration_s",
                    "mount_give_resolved_duration_s",
                    "mount_receive_resolved_duration_s",
                    "forage_search_resolved_duration_s",
                ]
            ],
            on="session_id",
            how="inner",
        )
        .merge(
            social[
                [
                    "session_id",
                    "session_duration_s",
                    "session_duration_quiet_masked_s",
                    "Groom solicit_duration_pct_session",
                    "Groom solicit_duration_pct_quiet_masked_p90",
                    "Mount give_duration_pct_session",
                    "Mount give_duration_pct_quiet_masked_p90",
                    "Mount receive_duration_pct_session",
                    "Mount receive_duration_pct_quiet_masked_p90",
                ]
            ],
            on="session_id",
            how="inner",
        )
        .merge(audio_summary, on="session_id", how="inner")
        .sort_values("date")
        .reset_index(drop=True)
    )

    base["analyzed_duration_s"] = base["session_duration_min"] * 60.0
    base["quiet_duration_s"] = base["duration_min_quiet_masked_p90"] * 60.0
    base["loud_only_duration_s"] = np.maximum(base["analyzed_duration_s"] - base["quiet_duration_s"], 0.0)

    base["groom_total_duration_s"] = base["groom_give_resolved_duration_s"] + base["groom_receive_resolved_duration_s"]
    base["groom_net_duration_s"] = base["groom_receive_resolved_duration_s"] - base["groom_give_resolved_duration_s"]
    base["forage_search_duration_s"] = base["forage_search_resolved_duration_s"]
    base["groom_give_duration_s_quiet"] = base["groom_give_pct_quiet_masked_p90"] * base["quiet_duration_s"] / 100.0
    base["groom_receive_duration_s_quiet"] = base["groom_receive_pct_quiet_masked_p90"] * base["quiet_duration_s"] / 100.0
    base["groom_total_duration_s_quiet"] = base["groom_total_pct_quiet_masked_p90"] * base["quiet_duration_s"] / 100.0
    base["groom_net_duration_s_quiet"] = base["groom_duration_net_receive_minus_give_pct_quiet_masked_p90"] * base["quiet_duration_s"] / 100.0
    base["groom_give_duration_s_loud"] = np.maximum(base["groom_give_resolved_duration_s"] - base["groom_give_duration_s_quiet"], 0.0)
    base["groom_receive_duration_s_loud"] = np.maximum(base["groom_receive_resolved_duration_s"] - base["groom_receive_duration_s_quiet"], 0.0)
    base["groom_total_duration_s_loud"] = np.maximum(base["groom_total_duration_s"] - base["groom_total_duration_s_quiet"], 0.0)
    base["groom_net_duration_s_loud"] = base["groom_receive_duration_s_loud"] - base["groom_give_duration_s_loud"]
    base["groom_give_resolved_duration_s_quiet"] = base["groom_give_duration_s_quiet"]
    base["groom_receive_resolved_duration_s_quiet"] = base["groom_receive_duration_s_quiet"]
    base["groom_total_duration_s_quiet"] = base["groom_total_duration_s_quiet"]
    base["groom_net_duration_s_quiet"] = base["groom_net_duration_s_quiet"]
    base["groom_give_resolved_duration_s_loud"] = base["groom_give_duration_s_loud"]
    base["groom_receive_resolved_duration_s_loud"] = base["groom_receive_duration_s_loud"]
    base["groom_total_duration_s_loud"] = base["groom_total_duration_s_loud"]
    base["groom_net_duration_s_loud"] = base["groom_net_duration_s_loud"]

    for prefix in ["Mount give", "Mount receive", "Groom solicit"]:
        safe = prefix.lower().replace(" ", "_")
        full_pct_col = f"{prefix}_duration_pct_session"
        quiet_pct_col = f"{prefix}_duration_pct_quiet_masked_p90"
        base[f"{safe}_duration_s"] = base[full_pct_col] * base["analyzed_duration_s"] / 100.0
        base[f"{safe}_duration_s_quiet"] = base[quiet_pct_col] * base["quiet_duration_s"] / 100.0
        base[f"{safe}_duration_s_loud"] = np.maximum(base[f"{safe}_duration_s"] - base[f"{safe}_duration_s_quiet"], 0.0)

    base["forage_search_duration_s_quiet"] = base["forage_search_duration_s__exclude_smoothed_loud_epochs"]
    base["forage_search_duration_s_loud"] = base["forage_search_duration_s__include_smoothed_loud_epochs_only"]
    base["travel_duration_s"] = base["travel_duration_s__full"]
    base["travel_duration_s_quiet"] = base["travel_duration_s__exclude_smoothed_loud_epochs"]
    base["travel_duration_s_loud"] = base["travel_duration_s__include_smoothed_loud_epochs_only"]
    base["rest_stationary_duration_s"] = base["rest_stationary_duration_s__full"]
    base["rest_stationary_duration_s_quiet"] = base["rest_stationary_duration_s__exclude_smoothed_loud_epochs"]
    base["rest_stationary_duration_s_loud"] = base["rest_stationary_duration_s__include_smoothed_loud_epochs_only"]
    base["scratch_duration_s"] = base["scratch_duration_s__full"]
    base["scratch_duration_s_quiet"] = base["scratch_duration_s__exclude_smoothed_loud_epochs"]
    base["scratch_duration_s_loud"] = base["scratch_duration_s__include_smoothed_loud_epochs_only"]
    base["vigilant_scan_duration_s"] = base["vigilant_scan_duration_s__full"]
    base["vigilant_scan_duration_s_quiet"] = base["vigilant_scan_duration_s__exclude_smoothed_loud_epochs"]
    base["vigilant_scan_duration_s_loud"] = base["vigilant_scan_duration_s__include_smoothed_loud_epochs_only"]
    base["attention_outside_duration_s"] = base["attention_outside_duration_s__full"]
    base["attention_outside_duration_s_quiet"] = base["attention_outside_duration_s__exclude_smoothed_loud_epochs"]
    base["attention_outside_duration_s_loud"] = base["attention_outside_duration_s__include_smoothed_loud_epochs_only"]
    base["hiccups_duration_s"] = base["hiccups_duration_s__full"]
    base["hiccups_duration_s_quiet"] = base["hiccups_duration_s__exclude_smoothed_loud_epochs"]
    base["hiccups_duration_s_loud"] = base["hiccups_duration_s__include_smoothed_loud_epochs_only"]
    base["loud_stress_composite_duration_s"] = base["loud_stress_composite_duration_s__full"]
    base["loud_stress_composite_duration_s_quiet"] = base["loud_stress_composite_duration_s__exclude_smoothed_loud_epochs"]
    base["loud_stress_composite_duration_s_loud"] = base["loud_stress_composite_duration_s__include_smoothed_loud_epochs_only"]

    return base


def _selection_duration_s(base: pd.DataFrame, selection: str) -> pd.Series:
    if selection in {"full", "exclude_vet_entry"}:
        return base["analyzed_duration_s"]
    if selection == "exclude_smoothed_loud_epochs":
        return base["quiet_duration_s"]
    if selection == "include_smoothed_loud_epochs_only":
        return base["loud_only_duration_s"]
    raise KeyError(selection)


def _resolve_duration(base: pd.DataFrame, stem: str, selection: str) -> pd.Series:
    if selection in {"full", "exclude_vet_entry"}:
        return base[stem]
    if selection == "exclude_smoothed_loud_epochs":
        return base[f"{stem}_quiet"]
    if selection == "include_smoothed_loud_epochs_only":
        return base[f"{stem}_loud"]
    raise KeyError(selection)


def build_branch_table(selection: str) -> pd.DataFrame:
    base = _build_base_table()
    duration_s = _selection_duration_s(base, selection)
    df = base.copy()
    df["data_selection"] = selection
    df["selected_duration_s"] = duration_s
    df["selected_duration_min"] = duration_s / 60.0
    df["groom_give_duration_s_selected"] = _resolve_duration(base, "groom_give_resolved_duration_s", selection)
    df["groom_receive_duration_s_selected"] = _resolve_duration(base, "groom_receive_resolved_duration_s", selection)
    df["groom_total_duration_s_selected"] = _resolve_duration(base, "groom_total_duration_s", selection)
    df["groom_net_duration_s_selected"] = _resolve_duration(base, "groom_net_duration_s", selection)
    df["mount_give_duration_s_selected"] = _resolve_duration(base, "mount_give_duration_s", selection)
    df["mount_receive_duration_s_selected"] = _resolve_duration(base, "mount_receive_duration_s", selection)
    df["groom_solicit_duration_s_selected"] = _resolve_duration(base, "groom_solicit_duration_s", selection)
    df["forage_search_duration_s_selected"] = _resolve_duration(base, "forage_search_duration_s", selection)
    df["travel_duration_s_selected"] = _resolve_duration(base, "travel_duration_s", selection)
    df["rest_stationary_duration_s_selected"] = _resolve_duration(base, "rest_stationary_duration_s", selection)
    df["scratch_duration_s_selected"] = _resolve_duration(base, "scratch_duration_s", selection)
    df["vigilant_scan_duration_s_selected"] = _resolve_duration(base, "vigilant_scan_duration_s", selection)
    df["attention_outside_duration_s_selected"] = _resolve_duration(base, "attention_outside_duration_s", selection)
    df["hiccups_duration_s_selected"] = _resolve_duration(base, "hiccups_duration_s", selection)
    df["loud_stress_composite_duration_s_selected"] = _resolve_duration(base, "loud_stress_composite_duration_s", selection)

    pct_specs = [
        ("groom_give_pct_selected", "groom_give_duration_s_selected"),
        ("groom_receive_pct_selected", "groom_receive_duration_s_selected"),
        ("groom_total_pct_selected", "groom_total_duration_s_selected"),
        ("mount_give_pct_selected", "mount_give_duration_s_selected"),
        ("mount_receive_pct_selected", "mount_receive_duration_s_selected"),
        ("groom_solicit_pct_selected", "groom_solicit_duration_s_selected"),
        ("forage_search_pct_selected", "forage_search_duration_s_selected"),
        ("travel_pct_selected", "travel_duration_s_selected"),
        ("rest_stationary_pct_selected", "rest_stationary_duration_s_selected"),
        ("scratch_pct_selected", "scratch_duration_s_selected"),
        ("vigilant_scan_pct_selected", "vigilant_scan_duration_s_selected"),
        ("attention_outside_pct_selected", "attention_outside_duration_s_selected"),
        ("hiccups_pct_selected", "hiccups_duration_s_selected"),
        ("loud_stress_composite_pct_selected", "loud_stress_composite_duration_s_selected"),
    ]
    for out_col, duration_col in pct_specs:
        df[out_col] = np.where(duration_s > 0, 100.0 * df[duration_col] / duration_s, np.nan)
    df["groom_net_pct_selected"] = np.where(duration_s > 0, 100.0 * df["groom_net_duration_s_selected"] / duration_s, np.nan)
    df["groom_reciprocity_selected"] = [
        reciprocity_score(recv, give)
        for recv, give in zip(df["groom_receive_duration_s_selected"], df["groom_give_duration_s_selected"])
    ]

    if selection in {"full", "exclude_vet_entry"}:
        df["groom_give_bouts_selected"] = df["groom_give_resolved_bouts"]
        df["groom_receive_bouts_selected"] = df["groom_receive_resolved_bouts"]
        df["groom_total_bouts_selected"] = df["groom_total_resolved_bouts"]
        df["groom_bout_net_selected"] = df["groom_bout_net_receive_minus_give"]
        df["groom_bout_reciprocity_selected"] = df["groom_bout_reciprocity_0to1"]
        df["groom_bout_mean_duration_selected_s"] = df["groom_total_bout_mean_duration_s"]
        df["groom_bout_median_duration_selected_s"] = df["groom_total_bout_median_duration_s"]
    elif selection == "exclude_smoothed_loud_epochs":
        df["groom_give_bouts_selected"] = df["groom_give_bouts_quiet_masked_p90"]
        df["groom_receive_bouts_selected"] = df["groom_receive_bouts_quiet_masked_p90"]
        df["groom_total_bouts_selected"] = df["groom_total_bouts_quiet_masked_p90"]
        df["groom_bout_net_selected"] = df["groom_bout_net_receive_minus_give_quiet_masked_p90"]
        df["groom_bout_reciprocity_selected"] = df["groom_bout_reciprocity_0to1_quiet_masked_p90"]
        df["groom_bout_mean_duration_selected_s"] = df["groom_total_bout_mean_duration_s_quiet_masked_p90"]
        df["groom_bout_median_duration_selected_s"] = df["groom_total_bout_median_duration_s_quiet_masked_p90"]
    else:
        df["groom_give_bouts_selected"] = np.nan
        df["groom_receive_bouts_selected"] = np.nan
        df["groom_total_bouts_selected"] = np.nan
        df["groom_bout_net_selected"] = np.nan
        df["groom_bout_reciprocity_selected"] = np.nan
        df["groom_bout_mean_duration_selected_s"] = np.nan
        df["groom_bout_median_duration_selected_s"] = np.nan

    if selection == "exclude_vet_entry":
        df = df.loc[df["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    return df.sort_values("date").reset_index(drop=True)


def load_all_branch_tables() -> dict[str, pd.DataFrame]:
    return {
        "full": build_branch_table("full"),
        "exclude_vet_entry": build_branch_table("exclude_vet_entry"),
        "exclude_smoothed_loud_epochs": build_branch_table("exclude_smoothed_loud_epochs"),
        "include_smoothed_loud_epochs_only": build_branch_table("include_smoothed_loud_epochs_only"),
    }


def build_minute_timecourse(selection: str) -> pd.DataFrame:
    audio = pd.read_csv(DERIVED_AUDIO, dtype={"session_id": str})
    session_map = load_unblinding_map()
    rows: list[dict[str, object]] = []
    for session_id, group in audio.groupby("session_id", sort=False):
        ordered = group.sort_values("elapsed_start_s").reset_index(drop=True)
        loud_mask, _, _ = compute_smoothed_loud_mask(ordered)
        if selection in {"full", "exclude_vet_entry"}:
            keep_mask = np.ones(len(ordered), dtype=bool)
        elif selection == "exclude_smoothed_loud_epochs":
            keep_mask = ~loud_mask
        else:
            keep_mask = loud_mask

        ordered = ordered.assign(keep=keep_mask)
        max_minute = int(np.ceil(float(ordered["elapsed_mid_min"].max()))) if not ordered.empty else 0
        for minute in range(max_minute + 1):
            cutoff_s = float(minute) * 60.0
            sub = ordered.loc[(ordered["elapsed_start_s"] <= cutoff_s) & ordered["keep"]].copy()
            give_s = float(sub["social_state"].eq("Groom give").sum())
            receive_s = float(sub["social_state"].eq("Groom receive").sum())
            rows.append(
                {
                    "session_id": str(session_id),
                    "elapsed_min": float(minute),
                    "cum_groom_give_duration_s": give_s,
                    "cum_groom_receive_duration_s": receive_s,
                    "cum_groom_total_duration_s": give_s + receive_s,
                    "cum_groom_net_duration_s": receive_s - give_s,
                }
            )
    timecourse = pd.DataFrame(rows)
    if selection == "exclude_vet_entry":
        timecourse = timecourse.loc[timecourse["session_id"] != VET_ENTRY_SESSION_ID].reset_index(drop=True)
    return session_map[["session_id", "condition", "date", "session_index"]].merge(timecourse, on="session_id", how="inner")
