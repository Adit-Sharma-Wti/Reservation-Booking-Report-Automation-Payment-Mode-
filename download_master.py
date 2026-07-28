# ============================================================
# DOWNLOAD MASTER — Step 1 Only
# download_master.py
# ============================================================

import sys
import logging
import json
import os
from pathlib import Path
from datetime import datetime

from config_loader import load_config
from downloader import run_downloader
from google_sheets_updater import update_google_sheet


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


def is_current_month_file(file_date_str: str) -> bool:
    """
    Returns True if the file_date matches today's month and year.
    Used to identify current month file on 1st of month
    when 2 files are downloaded.
    """
    if not file_date_str:
        return True  # Default: treat as current month

    today     = datetime.today()
    file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

    return (
        file_date.year  == today.year and
        file_date.month == today.month
    )


def main():
    logger   = setup_logger()
    run_date = datetime.today()

    logger.info("=" * 70)
    logger.info("  STEP 1 — DOWNLOAD BOOKING DATA")
    logger.info(
        f"  Run Date : {run_date.strftime('%d-%b-%Y %H:%M:%S')}"
    )
    logger.info("=" * 70)

    config = load_config("config.ini")

    download_dir = config["PATHS"]["downloads_source_folder"]
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    # ── Run Downloader ─────────────────────────────────────
    results = run_downloader(config, logger)

    # ── Validate Results ───────────────────────────────────
    all_success  = all(r["success"] for r in results)
    failed_tasks = [
        i + 1
        for i, r in enumerate(results)
        if not r["success"]
    ]

    if not all_success:
        logger.error(
            f"❌ Download FAILED for task(s): {failed_tasks}"
        )
        sys.exit(1)

    # ── Build Handoff ──────────────────────────────────────
    files = [
        {
            "file_path": r["file_path"],
            "file_date": r["file_date"],
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

    handoff_path = Path("/tmp/handoff.json")
    with open(handoff_path, "w") as f:
        json.dump(handoff, f, indent=2)

    # ── Log Each Downloaded File ───────────────────────────
    for item in files:
        logger.info(
            f"✅ Downloaded : {Path(item['file_path']).name}"
            f" | file_date: {item['file_date']}"
        )

    logger.info(f"✅ Handoff saved : {handoff_path}")
    logger.info(f"✅ Total files   : {len(files)}")

    # ── Google Sheet Update ────────────────────────────────
    logger.info("=" * 70)
    logger.info("  GOOGLE SHEET UPDATE")
    logger.info("=" * 70)

    # Get secrets from environment
    service_account_json = os.environ.get(
        "GOOGLE_SERVICE_ACCOUNT_JSON", ""
    ).strip()
    sheet_id = os.environ.get(
        "GOOGLE_SHEET_ID", ""
    ).strip()

    if not service_account_json:
        logger.error(
            "[SHEETS] ❌ GOOGLE_SERVICE_ACCOUNT_JSON secret "
            "is missing — skipping sheet update."
        )
    elif not sheet_id:
        logger.error(
            "[SHEETS] ❌ GOOGLE_SHEET_ID secret "
            "is missing — skipping sheet update."
        )
    else:
        # ── Find current month file ────────────────────────
        current_month_file = None

        for item in files:
            if is_current_month_file(item["file_date"]):
                current_month_file = item["file_path"]
                logger.info(
                    f"[SHEETS] Current month file identified: "
                    f"{Path(current_month_file).name}"
                )
                break

        if not current_month_file:
            logger.warning(
                "[SHEETS] ⚠️  No current month file found "
                "— skipping sheet update."
            )
        else:
            # ── Update Sheet ───────────────────────────────
            success = update_google_sheet(
                file_path            = current_month_file,
                service_account_json = service_account_json,
                sheet_id             = sheet_id,
                sheet_name           = "BOOKING",
                logger               = logger,
            )

            if success:
                logger.info(
                    "✅ Google Sheet updated successfully!"
                )
            else:
                # Option B — log error but continue
                logger.error(
                    "❌ Google Sheet update FAILED. "
                    "Email job will still proceed."
                )

    logger.info("=" * 70)
    logger.info("✅ Download step complete.")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
