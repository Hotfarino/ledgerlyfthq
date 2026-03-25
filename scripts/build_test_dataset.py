#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd


def read_sheet(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")
    if suffix in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return pd.read_excel(path, dtype=str, engine="openpyxl").fillna("")
    raise ValueError(f"Unsupported file type: {path}")


def write_sheet(df: pd.DataFrame, output_path: Path) -> None:
    suffix = output_path.suffix.lower()
    if suffix == ".csv":
        df.to_csv(output_path, index=False)
        return
    if suffix == ".xlsx":
        df.to_excel(output_path, index=False, engine="openpyxl")
        return
    raise ValueError("Output must be .csv or .xlsx")


def build_dataset(
    inputs: List[Path],
    output_path: Path,
    duplicate_count: int,
    seed: int,
    shuffle: bool,
    include_source_columns: bool,
    include_duplicate_markers: bool,
) -> tuple[int, int]:
    frames: List[pd.DataFrame] = []
    for file_path in inputs:
        df = read_sheet(file_path).copy()
        df.columns = [str(col).strip() for col in df.columns]

        if include_source_columns:
            df["__source_file"] = file_path.name
            df["__source_row_number"] = list(range(1, len(df) + 1))

        frames.append(df)

    if not frames:
        raise ValueError("No input data loaded.")

    merged = pd.concat(frames, ignore_index=True, sort=False).fillna("")
    original_rows = len(merged)

    if include_duplicate_markers:
        merged["__synthetic_duplicate"] = "no"
        merged["__duplicate_of_index"] = ""

    if duplicate_count > 0:
        if original_rows == 0:
            raise ValueError("Cannot generate duplicates from an empty dataset.")

        sampled_indices = merged.sample(n=duplicate_count, replace=True, random_state=seed).index.tolist()
        duplicates = merged.loc[sampled_indices].copy()
        if include_duplicate_markers:
            duplicates["__synthetic_duplicate"] = "yes"
            duplicates["__duplicate_of_index"] = sampled_indices

        merged = pd.concat([merged, duplicates], ignore_index=True, sort=False).fillna("")

    if shuffle:
        merged = merged.sample(frac=1, random_state=seed).reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_sheet(merged, output_path)
    return original_rows, len(merged)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge multiple CSV/XLSX files and inject synthetic duplicate rows for testing."
    )
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="Input CSV/XLSX files to merge.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output file path (.csv or .xlsx).",
    )
    parser.add_argument(
        "--duplicate-count",
        type=int,
        default=0,
        help="Number of duplicate rows to inject.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic duplicate selection and optional shuffle.",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle final output rows after merge and duplicate injection.",
    )
    parser.add_argument(
        "--no-source-columns",
        action="store_true",
        help="Do not add __source_file and __source_row_number columns.",
    )
    parser.add_argument(
        "--no-duplicate-markers",
        action="store_true",
        help="Do not add duplicate marker columns.",
    )
    args = parser.parse_args()
    if args.duplicate_count < 0:
        raise ValueError("--duplicate-count must be >= 0")
    return args


def main() -> None:
    args = parse_args()

    input_paths = [Path(item).expanduser().resolve() for item in args.inputs]
    for path in input_paths:
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")

    output_path = Path(args.output).expanduser().resolve()
    before_rows, after_rows = build_dataset(
        inputs=input_paths,
        output_path=output_path,
        duplicate_count=args.duplicate_count,
        seed=args.seed,
        shuffle=args.shuffle,
        include_source_columns=not args.no_source_columns,
        include_duplicate_markers=not args.no_duplicate_markers,
    )

    print("Dataset build complete.")
    print(f"Output: {output_path}")
    print(f"Input files: {len(input_paths)}")
    print(f"Rows before duplicates: {before_rows}")
    print(f"Synthetic duplicates added: {args.duplicate_count}")
    print(f"Rows after duplicates: {after_rows}")


if __name__ == "__main__":
    main()
