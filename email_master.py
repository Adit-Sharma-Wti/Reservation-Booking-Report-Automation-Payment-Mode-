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

    # Support both old (file_path) and new (file_paths) format
    if "file_paths" in handoff:
        file_paths = handoff["file_paths"]
    elif "file_path" in handoff:
        file_paths = [handoff["file_path"]]
    else:
        logger.error("❌ No file path found in handoff.json")
        sys.exit(1)

    logger.info(f"📂 Files to process : {len(file_paths)}")
    logger.info(
        f"📅 Downloaded at    : {handoff['run_date']}"
    )

    output_dir = config["PATHS"]["root_output_folder"]
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Process each file sequentially
    # On 1st of month: prev month file first, then current
    for idx, file_path in enumerate(file_paths, start=1):
        logger.info("=" * 70)
        logger.info(
            f"  Processing file {idx}/{len(file_paths)}: "
            f"{Path(file_path).name}"
        )
        logger.info("=" * 70)

        success = run_processor(config, logger, file_path)

        if not success:
            logger.error(
                f"❌ Processing FAILED for: "
                f"{Path(file_path).name}"
            )
            sys.exit(1)

        logger.info(
            f"✅ File {idx}/{len(file_paths)} complete."
        )

    logger.info("=" * 70)
    logger.info("✅ All files processed and emails sent.")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
