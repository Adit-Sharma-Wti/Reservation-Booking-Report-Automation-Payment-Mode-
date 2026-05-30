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

    # Load config with secrets injected
    config = load_config("config.ini")

    # Ensure download directory exists
    download_dir = config["PATHS"]["downloads_source_folder"]
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    # Run downloader
    success, file_path, is_full_month = run_downloader(config, logger)

    if not success:
        logger.error("❌ Download FAILED.")
        sys.exit(1)

    # Save file path to handoff file
    # This file is uploaded as artifact and
    # downloaded by email step
    handoff = {
        "file_path"     : file_path,
        "is_full_month" : is_full_month,
        "run_date"      : run_date.strftime("%Y-%m-%d %H:%M:%S"),
        "downloaded_by" : "download_master.py",
    }

    handoff_path = Path("/tmp/handoff.json")
    with open(handoff_path, "w") as f:
        json.dump(handoff, f, indent=2)

    logger.info(f"✅ Download complete: {Path(file_path).name}")
    logger.info(f"✅ Handoff saved: {handoff_path}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()