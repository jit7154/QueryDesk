#!/usr/bin/env python3
"""Download structured retail data from Kaggle using official API."""

import os
from pathlib import Path
import sys
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "raw"
FALLBACK_DATASET = "olistbr/brazilian-ecommerce"


def get_authenticated_api() -> KaggleApi:
    """Initialize and authenticate Kaggle API client."""
    api = KaggleApi()
    api.authenticate()
    return api


def check_user_datasets(api: KaggleApi, username: str) -> str | None:
    """Check user's Kaggle profile for relevant retail datasets."""
    print(f"Checking Kaggle account '{username}' for datasets...")
    try:
        datasets = api.dataset_list(user=username)
        for ds in datasets:
            ref = getattr(ds, "ref", "")
            title = getattr(ds, "title", "").lower()
            if any(k in title for k in ["retail", "ecommerce", "e-commerce", "orders", "supply"]):
                print(f"Found suitable dataset in user account: {ref}")
                return ref
        print("No matching retail/e-commerce dataset found in user profile.")
        return None
    except Exception as exc:
        print(f"Error checking user account: {exc}")
        return None


def download_and_extract(api: KaggleApi, dataset_ref: str, target_dir: Path) -> None:
    """Download dataset zip archive and extract CSV files."""
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading dataset '{dataset_ref}' into {target_dir}...")
    api.dataset_download_files(dataset_ref, path=str(target_dir), unzip=True)
    print("Download and extraction complete.")


def main() -> None:
    username = os.environ.get("KAGGLE_USERNAME", "prabhujitsingh")
    api = get_authenticated_api()
    dataset_ref = check_user_datasets(api, username)
    if not dataset_ref:
        print(f"Falling back to public reference dataset: {FALLBACK_DATASET}")
        dataset_ref = FALLBACK_DATASET

    download_and_extract(api, dataset_ref, RAW_DATA_DIR)

    csv_files = list(RAW_DATA_DIR.glob("*.csv"))
    print(f"Extracted {len(csv_files)} CSV files:")
    for f in sorted(csv_files):
        print(f" - {f.name} ({f.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
