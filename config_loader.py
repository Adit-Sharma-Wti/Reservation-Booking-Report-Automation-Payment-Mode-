# ============================================================
# CONFIG LOADER — Injects Secrets from Environment Variables
# config_loader.py
# ============================================================

import os
import configparser
from pathlib import Path


def load_config(path: str = "config.ini") -> configparser.ConfigParser:
    """
    Loads config.ini normally (no placeholders).
    Then overrides credential fields directly from
    environment variables injected by GitHub Actions secrets.

    This approach avoids GitHub secret masking issue
    where *** corrupts configparser parsing.
    """
    if not Path(path).exists():
        raise FileNotFoundError(
            f"config.ini not found at: {path}"
        )

    # Parse config normally — no secrets in file
    config = configparser.ConfigParser()
    config.read(path, encoding="utf-8")

    # ── Inject DOWNLOADER secrets ──────────────────────────
    wisx_user = os.environ.get("WISX_USER_ID", "").strip()
    wisx_pass = os.environ.get("WISX_PASSWORD", "").strip()

    if wisx_user:
        config["DOWNLOADER"]["user_id"] = wisx_user
    if wisx_pass:
        config["DOWNLOADER"]["password"] = wisx_pass

    # ── Inject SMTP secrets ────────────────────────────────
    smtp_email = os.environ.get("SMTP_SENDER_EMAIL", "").strip()
    smtp_pass  = os.environ.get("SMTP_SENDER_PASSWORD", "").strip()

    if smtp_email:
        config["SMTP"]["sender_email"] = smtp_email
    if smtp_pass:
        config["SMTP"]["sender_password"] = smtp_pass

    # ── Inject EMAIL recipient secrets ─────────────────────
    linkedin_to = os.environ.get("EMAIL_LINKEDIN_TO", "").strip()
    linkedin_cc = os.environ.get("EMAIL_LINKEDIN_CC", "").strip()
    btc_to      = os.environ.get("EMAIL_BTC_TO", "").strip()
    btc_cc      = os.environ.get("EMAIL_BTC_CC", "").strip()
    nonbtc_to   = os.environ.get("EMAIL_NONBTC_TO", "").strip()
    nonbtc_cc   = os.environ.get("EMAIL_NONBTC_CC", "").strip()
    # ── Inject Google Sheets secrets ──────────────────────
    # These are read directly from env in google_sheets_updater.py
    # No config.ini section needed — just validate presence here
    google_sa_json = os.environ.get(
        "GOOGLE_SERVICE_ACCOUNT_JSON", ""
    ).strip()
    google_sheet_id = os.environ.get(
        "GOOGLE_SHEET_ID", ""
    ).strip()

    if not google_sa_json:
        print(
            "⚠️  WARNING: GOOGLE_SERVICE_ACCOUNT_JSON not set "
            "— Google Sheet update will be skipped."
        )
    if not google_sheet_id:
        print(
            "⚠️  WARNING: GOOGLE_SHEET_ID not set "
            "— Google Sheet update will be skipped."
        )

    if linkedin_to:
        config["EMAIL_LINKEDIN"]["to"] = linkedin_to
    if linkedin_cc:
        config["EMAIL_LINKEDIN"]["cc"] = linkedin_cc

    if btc_to:
        config["EMAIL_BTC"]["to"] = btc_to
    if btc_cc:
        config["EMAIL_BTC"]["cc"] = btc_cc

    if nonbtc_to:
        config["EMAIL_NONBTC"]["to"] = nonbtc_to
    if nonbtc_cc:
        config["EMAIL_NONBTC"]["cc"] = nonbtc_cc

    # ── Validate critical secrets present ─────────────────
    missing = []
    if not config["DOWNLOADER"]["user_id"]:
        missing.append("WISX_USER_ID")
    if not config["DOWNLOADER"]["password"]:
        missing.append("WISX_PASSWORD")
    if not config["SMTP"]["sender_email"]:
        missing.append("SMTP_SENDER_EMAIL")
    if not config["SMTP"]["sender_password"]:
        missing.append("SMTP_SENDER_PASSWORD")

    if missing:
        print(
            f"⚠️  WARNING: Missing critical secrets: "
            f"{', '.join(missing)}"
        )
    else:
        print("✅ All critical secrets loaded successfully.")

    return config
