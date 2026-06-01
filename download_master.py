# ============================================================
# DOWNLOAD MASTER — Step 1 Only
# download_master.py
# ============================================================

import sys
import logging
import json
from pathlib import Path
from datetime import datetime

from config_loader import load_config
from downloader import run_downloader


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("Downloader")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-8s]  %(message)s",
        datefmt="%d-%b-%Y %H:%M:%S"
    )
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    return logger


def main():
    logger = setup_logger()
    run_date = datetime.today()

    logger.info("=" * 70)
    logger.info("  STEP 1 — DOWNLOAD BOOKING DATA")
    logger.info(f"  Run Date : {run_date.strftime('%d-%b-%Y %H:%M:%S')}")
    logger.info("=" * 70)

    config = load_config("config.ini")

    download_dir = config["PATHS"]["downloads_source_folder"]
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    # Returns LIST of (success, file_path, is_full_month)
    results = run_downloader(config, logger)

    # Check all tasks succeeded
    all_success   = all(r[0] for r in results)
    failed_tasks  = [i+1 for i, r in enumerate(results) if not r[0]]

    if not all_success:
        logger.error(
            f"❌ Download FAILED for task(s): {failed_tasks}"
        )
        sys.exit(1)

    # Build handoff with ALL downloaded files
    # Email step will process each file sequentially
    files = [
        {
            "file_path" : r["file_path"],
            "file_date" : r["file_date"],
        }
        for r in results
    ]
    
    handoff = {
        "files"         : files,
        "is_full_month" : True,
        "run_date"      : run_date.strftime("%Y-%m-%d %H:%M:%S"),
        "downloaded_by" : "download_master.py",
        "task_count"    : len(results),
    }
    
    # Update logger lines
    for item in files:
        logger.info(
            f"✅ Downloaded : {Path(item['file_path']).name}"
            f" (file_date: {item['file_date']})"
        )
    logger.info(f"✅ Handoff saved : {handoff_path}")
    logger.info(f"✅ Total files   : {len(files)}")

    handoff_path = Path("/tmp/handoff.json")
    with open(handoff_path, "w") as f:
        json.dump(handoff, f, indent=2)

    for file_path in file_paths:
        logger.info(f"✅ Downloaded: {Path(file_path).name}")
    logger.info(f"✅ Handoff saved: {handoff_path}")
    logger.info(f"✅ Total files  : {len(file_paths)}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
