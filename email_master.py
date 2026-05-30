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

    # Load config with secrets injected
    config = load_config("config.ini")

    # Read handoff file from download step
    handoff_path = Path("/tmp/handoff.json")

    if not handoff_path.exists():
        logger.error(
            "❌ Handoff file not found. "
            "Did the download step complete successfully?"
        )
        sys.exit(1)

    with open(handoff_path, "r") as f:
        handoff = json.load(f)

    file_path = handoff["file_path"]
    logger.info(f"📂 Processing file: {Path(file_path).name}")
    logger.info(
        f"📅 Originally downloaded at: {handoff['run_date']}"
    )

    # Ensure output directories exist
    output_dir = config["PATHS"]["root_output_folder"]
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Run processor + emailer
    success = run_processor(config, logger, file_path)

    if not success:
        logger.error("❌ Processing or Email step FAILED.")
        sys.exit(1)

    logger.info("✅ Processing and Email complete.")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()