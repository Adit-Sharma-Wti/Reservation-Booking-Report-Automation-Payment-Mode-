# ============================================================
# EMAIL MASTER — Step 2 + 3 Only
# email_master.py
# ============================================================

import sys
import logging
import json
from pathlib import Path
from datetime import datetime

from config_loader import load_config
from processor import run_processor


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("EmailSender")
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
    logger.info("  STEP 2+3 — PROCESS DATA & SEND EMAILS")
    logger.info(f"  Run Date : {run_date.strftime('%d-%b-%Y %H:%M:%S')}")
    logger.info("=" * 70)

    config = load_config("config.ini")

    handoff_path = Path("/tmp/handoff.json")
    if not handoff_path.exists():
        logger.error(
            "❌ Handoff file not found. "
            "Did the download step complete successfully?"
        )
        sys.exit(1)

    with open(handoff_path, "r") as f:
        handoff = json.load(f)

    # ── Support all handoff formats ────────────────────────
    if "files" in handoff:
        # New format: list of {file_path, file_date}
        files = handoff["files"]

    elif "file_paths" in handoff:
        # Old format: list of paths only, no file_date
        files = [
            {
                "file_path": fp,
                "file_date": None,
            }
            for fp in handoff["file_paths"]
        ]

    elif "file_path" in handoff:
        # Oldest format: single path only
        files = [
            {
                "file_path": handoff["file_path"],
                "file_date": None,
            }
        ]

    else:
        logger.error(
            "❌ No file path found in handoff.json"
        )
        sys.exit(1)

    logger.info(f"📂 Files to process : {len(files)}")
    logger.info(
        f"📅 Downloaded at    : {handoff['run_date']}"
    )

    output_dir = config["PATHS"]["root_output_folder"]
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ── Process each file sequentially ────────────────────
    # On 1st of month: prev month file first, then current
    for idx, item in enumerate(files, start=1):
        file_path     = item["file_path"]
        file_date_str = item.get("file_date", None)

        # Parse file_date string back to datetime
        if file_date_str:
            file_date = datetime.strptime(
                file_date_str, "%Y-%m-%d"
            )
        else:
            file_date = None

        logger.info("=" * 70)
        logger.info(
            f"  Processing file {idx}/{len(files)}: "
            f"{Path(file_path).name}"
        )
        if file_date:
            logger.info(
                f"  File month  : "
                f"{file_date.strftime('%B %Y')}"
            )
        logger.info("=" * 70)

        # Pass file_date so processor uses correct
        # month folder, store path and report label
        success = run_processor(
            config, logger, file_path, file_date
        )

        if not success:
            logger.error(
                f"❌ Processing FAILED for: "
                f"{Path(file_path).name}"
            )
            sys.exit(1)

        logger.info(
            f"✅ File {idx}/{len(files)} complete."
        )

    logger.info("=" * 70)
    logger.info("✅ All files processed and emails sent.")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
