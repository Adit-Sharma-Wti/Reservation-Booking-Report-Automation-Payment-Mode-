# ============================================================
# GOOGLE SHEETS UPDATER
# google_sheets_updater.py
# ============================================================

import json
import logging
import tempfile
import os
import pandas as pd
import gspread

from pathlib import Path
from datetime import datetime
from google.oauth2.service_account import Credentials


# ── Columns to write to Google Sheet ──────────────────────
SHEET_COLUMNS = [
    "BookingNo",
    "Corporate",
    "CabRequiredOn",
    "Status",
    "Hub",
    "Run",
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ============================================================
# MAIN UPDATER FUNCTION
# ============================================================

def update_google_sheet(
    file_path: str,
    service_account_json: str,
    sheet_id: str,
    sheet_name: str = "BOOKING",
    logger: logging.Logger = None,
) -> bool:
    """
    Reads the downloaded Excel file, extracts only the
    required 6 columns, clears Google Sheet from Row 2
    (keeps header), and writes fresh data.

    Args:
        file_path           : Path to downloaded Excel file
        service_account_json: Full JSON string of service account
        sheet_id            : Google Spreadsheet ID
        sheet_name          : Target sheet tab name (BOOKING)
        logger              : Logger instance

    Returns:
        True if successful, False if failed
    """

    if logger is None:
        logger = logging.getLogger("GoogleSheets")

    try:
        logger.info("[SHEETS] Starting Google Sheet update...")
        logger.info(f"[SHEETS] File     : {Path(file_path).name}")
        logger.info(f"[SHEETS] Sheet    : {sheet_name}")

        # ── Step 1: Read Excel file ────────────────────────
        logger.info("[SHEETS] Reading Excel file...")
        df = pd.read_excel(file_path, dtype=str)
        df.columns = df.columns.str.strip()
        logger.info(f"[SHEETS] Total rows in file : {len(df)}")

        # ── Step 2: Validate required columns exist ────────
        missing_cols = [
            col for col in SHEET_COLUMNS
            if col not in df.columns
        ]
        if missing_cols:
            logger.error(
                f"[SHEETS] ❌ Missing columns in Excel: "
                f"{missing_cols}"
            )
            return False

        # ── Step 3: Extract only required columns ──────────
        df_sheet = df[SHEET_COLUMNS].copy()

        # Clean data
        for col in df_sheet.columns:
            df_sheet[col] = (
                df_sheet[col]
                .fillna("")
                .astype(str)
                .str.strip()
            )

        logger.info(
            f"[SHEETS] Rows to write : {len(df_sheet)}"
        )

        # ── Step 4: Authenticate with Google ──────────────
        logger.info("[SHEETS] Authenticating with Google...")

        # Write JSON to a temp file (gspread needs file path)
        sa_dict = json.loads(service_account_json)

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
        ) as tmp:
            json.dump(sa_dict, tmp)
            tmp_path = tmp.name

        try:
            creds = Credentials.from_service_account_file(
                tmp_path,
                scopes=SCOPES,
            )
        finally:
            # Always delete temp file after use
            os.unlink(tmp_path)

        client = gspread.authorize(creds)
        logger.info("[SHEETS] ✅ Authenticated successfully!")

        # ── Step 5: Open Sheet ─────────────────────────────
        logger.info(
            f"[SHEETS] Opening spreadsheet ID: {sheet_id}"
        )
        spreadsheet = client.open_by_key(sheet_id)
        worksheet   = spreadsheet.worksheet(sheet_name)
        logger.info(
            f"[SHEETS] ✅ Opened sheet: {sheet_name}"
        )

        # ── Step 6: Clear from Row 2 (keep header) ────────
        logger.info(
            "[SHEETS] Clearing existing data (keeping header)..."
        )

        # Get current last row to know range to clear
        all_values  = worksheet.get_all_values()
        total_rows  = len(all_values)

        if total_rows > 1:
            # Clear from row 2 to last row
            # Using a large number to ensure all data cleared
            worksheet.batch_clear([f"A2:Z{max(total_rows, 10000)}"])
            logger.info(
                f"[SHEETS] Cleared rows 2 to {total_rows}"
            )
        else:
            logger.info(
                "[SHEETS] Sheet has only header — nothing to clear"
            )

        # ── Step 7: Write new data ─────────────────────────
        if df_sheet.empty:
            logger.warning(
                "[SHEETS] ⚠️  No data to write — sheet cleared only"
            )
            return True

        # Convert DataFrame to list of lists
        rows_to_write = df_sheet.values.tolist()

        # Write starting from Row 2 (A2)
        worksheet.update(
            range_name=f"A2",
            values=rows_to_write,
        )

        logger.info(
            f"[SHEETS] ✅ Written {len(rows_to_write)} rows "
            f"to sheet '{sheet_name}'"
        )
        logger.info("[SHEETS] ✅ Google Sheet update complete!")
        return True

    except gspread.exceptions.SpreadsheetNotFound:
        logger.error(
            f"[SHEETS] ❌ Spreadsheet not found. "
            f"Check GOOGLE_SHEET_ID secret."
        )
        return False

    except gspread.exceptions.WorksheetNotFound:
        logger.error(
            f"[SHEETS] ❌ Sheet tab '{sheet_name}' not found. "
            f"Check sheet name."
        )
        return False

    except gspread.exceptions.APIError as e:
        logger.error(
            f"[SHEETS] ❌ Google API error: {e}"
        )
        return False

    except json.JSONDecodeError:
        logger.error(
            "[SHEETS] ❌ Invalid service account JSON. "
            "Check GOOGLE_SERVICE_ACCOUNT_JSON secret."
        )
        return False

    except Exception as e:
        logger.exception(
            f"[SHEETS] ❌ Unexpected error: {e}"
        )
        return False
