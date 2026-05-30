# ============================================================
# BOOKING DATA DOWNLOADER
# downloader.py
# ============================================================

from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import time
import calendar
import configparser
import logging
from pathlib import Path


def run_downloader(
    config: configparser.ConfigParser,
    logger: logging.Logger
) -> tuple:
    """
    Downloads booking data from the WISX portal.

    Date range rule (CORRECTED):
      - From date: ALWAYS 1st day of the current month
      - To date  : ALWAYS last day of the current month

      Examples:
        • Run on 02-May-2026 → 01-May-2026 to 31-May-2026
        • Run on 28-May-2026 → 01-May-2026 to 31-May-2026
        • Run on 01-Jun-2026 → 01-Jun-2026 to 30-Jun-2026
        • Run on 15-Jun-2026 → 01-Jun-2026 to 30-Jun-2026

      This guarantees NO DATA IS MISSED regardless of
      which day or time the scheduler runs.

    Returns:
        (success: bool, file_path: str, is_full_month: bool)
    """

    # ── Read config ───────────────────────────────────────────
    login_url         = config["DOWNLOADER"]["login_url"].strip()
    report_url        = config["DOWNLOADER"]["report_url"].strip()
    change_fiscal_url = config["DOWNLOADER"]["change_fiscal_url"].strip()
    logout_url        = config["DOWNLOADER"]["logout_url"].strip()
    user_id           = config["DOWNLOADER"]["user_id"].strip()
    password          = config["DOWNLOADER"]["password"].strip()
    branch_id         = config["DOWNLOADER"]["branch_id"].strip()
    headless          = config["DOWNLOADER"].getboolean("headless")
    download_dir      = config["PATHS"]["downloads_source_folder"].strip()

    os.makedirs(download_dir, exist_ok=True)

    # ── Determine date range (CORRECTED RULE) ──────────────────
    # Rule:
    #   - From date : ALWAYS 1st of current month
    #   - To date   : ALWAYS last day of current month
    #
    # Examples:
    #   • Run on 02-May-2026 → 01-May-2026 to 31-May-2026
    #   • Run on 28-May-2026 → 01-May-2026 to 31-May-2026
    #   • Run on 01-Jun-2026 → 01-Jun-2026 to 30-Jun-2026
    #   • Run on 15-Jun-2026 → 01-Jun-2026 to 30-Jun-2026
    #
    # This ensures NO DATA IS MISSED regardless of which day
    # the scheduler runs (morning or night).
    # ────────────────────────────────────────────────────────────

    today = datetime.now().date()

    # From = 1st day of current month (ALWAYS)
    from_date = today.replace(day=1)

    # To = last day of current month (ALWAYS)
    last_day_num = calendar.monthrange(today.year, today.month)[1]
    to_date = today.replace(day=last_day_num)

    # is_full_month is now ALWAYS True since we always
    # download the complete month data
    is_full_month = True

    # ── Build filename ────────────────────────────────────────
    # Format: Bookings_Data_May_2026_(Complete May 2026).xlsx
    # Same filename every day within same month so it gets
    # overwritten with latest data each run — no stale files.
    month_label         = from_date.strftime("%B_%Y")
    month_label_display = from_date.strftime("%B %Y")
    filename  = (
        f"Bookings_Data_{month_label}"
        f"_(Complete {month_label_display}).xlsx"
    )

    file_path = os.path.join(download_dir, filename)

    logger.info("-" * 60)
    logger.info("[DOWNLOADER] Starting booking data download...")
    logger.info("[DOWNLOADER] Mode     : Full Month (Complete Month Always)")
    logger.info(
        f"[DOWNLOADER] Range    : "
        f"{from_date.strftime('%d-%m-%Y')} → {to_date.strftime('%d-%m-%Y')}"
    )
    logger.info(f"[DOWNLOADER] Filename : {filename}")
    logger.info(f"[DOWNLOADER] Save To  : {download_dir}")

    # ── IMPORTANT NOTE on file existence check ─────────────────
    # We do NOT skip if the file already exists because:
    #   - Same filename is reused every day within same month
    #   - We want fresh/latest data every run
    #   - Old file will be overwritten with updated data
    # ──────────────────────────────────────────────────────────
    if Path(file_path).exists():
        logger.info(
            f"[DOWNLOADER] File already exists: {filename}. "
            f"Will overwrite with latest data for complete month."
        )

    # ── Browser automation ────────────────────────────────────
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(accept_downloads=True)
            page    = context.new_page()

            # LOGIN
            logger.info("[DOWNLOADER] Logging in to WISX portal...")
            page.goto(login_url)
            page.fill("#Email",    user_id)
            page.click("#Password")
            page.fill("#Password", password)
            page.locator("input[type='submit'][value='Log in']").click()
            page.wait_for_load_state("networkidle")
            logger.info("[DOWNLOADER] ✅ Login successful!")

            # FISCAL YEAR CHECK
            current_fiscal = _get_current_fiscal_year(
                page, change_fiscal_url, logger
            )
            target_fiscal = _get_fiscal_year_for_date(from_date)

            logger.info(
                f"[DOWNLOADER] Current fiscal : {current_fiscal}"
            )
            logger.info(
                f"[DOWNLOADER] Required fiscal: {target_fiscal}"
            )

            if current_fiscal != target_fiscal:
                _switch_fiscal_year(
                    page, change_fiscal_url, target_fiscal, logger
                )
            else:
                logger.info(
                    "[DOWNLOADER] ✅ Fiscal year correct. No switch needed."
                )

            # DOWNLOAD REPORT
            logger.info("[DOWNLOADER] Navigating to report page...")
            page.goto(report_url)
            page.wait_for_selector("#FromDate")

            page.select_option("#BranchID", value=branch_id)

            page.eval_on_selector(
                "#FromDate", "el => el.removeAttribute('readonly')"
            )
            page.eval_on_selector(
                "#ToDate", "el => el.removeAttribute('readonly')"
            )

            _select_date(
                page, "#FromDate",
                datetime(from_date.year, from_date.month, from_date.day)
            )
            _select_date(
                page, "#ToDate",
                datetime(to_date.year, to_date.month, to_date.day)
            )

            logger.info("[DOWNLOADER] Triggering file download...")

            with page.expect_download(timeout=0) as dl:
                page.click(
                    "input[type='submit'].btn.btn-success",
                    no_wait_after=True
                )

            download = dl.value
            download.save_as(file_path)
            logger.info(f"[DOWNLOADER] ✅ File downloaded: {filename}")

            # LOGOUT
            logger.info("[DOWNLOADER] Logging out...")
            page.goto(logout_url)
            page.wait_for_load_state("networkidle")
            logger.info("[DOWNLOADER] ✅ Logged out successfully!")

            # CLEANUP
            page.close()
            context.close()
            browser.close()

        return True, file_path, is_full_month

    except Exception as e:
        logger.exception(f"[DOWNLOADER] ❌ Download failed: {e}")
        return False, "", is_full_month


# ============================================================
# PRIVATE HELPER FUNCTIONS
# ============================================================

def _select_date(page, selector: str, target_date: datetime):
    """Interacts with datepicker to select a specific date."""
    page.click(selector)
    page.wait_for_selector(".datepicker-days")

    target_month_year = target_date.strftime("%B %Y")
    target_day        = str(target_date.day)
    max_iterations    = 192
    iteration         = 0

    while iteration < max_iterations:
        current_month_year = page.locator(
            ".datepicker-days .datepicker-switch"
        ).inner_text()

        if current_month_year == target_month_year:
            break
        elif datetime.strptime(current_month_year, "%B %Y") > datetime(
            target_date.year, target_date.month, 1
        ):
            page.locator(".datepicker-days th.prev").click()
        else:
            page.locator(".datepicker-days th.next").click()

        iteration += 1
        time.sleep(0.15)

    final_month = page.locator(
        ".datepicker-days .datepicker-switch"
    ).inner_text()

    if final_month != target_month_year:
        raise RuntimeError(
            f"Could not navigate to {target_month_year}. "
            f"Stuck at {final_month}."
        )

    page.locator(
        f".datepicker-days td.day:not(.old):not(.new)"
        f":text-is('{target_day}')"
    ).click()
    page.mouse.click(10, 10)


def _get_fiscal_year_for_date(target_date) -> str:
    """Returns fiscal year string like '2025-2026'."""
    if target_date.month >= 4:
        return f"{target_date.year}-{target_date.year + 1}"
    return f"{target_date.year - 1}-{target_date.year}"


def _find_fiscal_selector(page) -> str:
    """Finds the fiscal year dropdown selector."""
    candidates = [
        "#FiscalYear", "select#FiscalYear",
        "select[name='FiscalYear']", "#FiscalYearId",
        "select#FiscalYearId", "select[name='FiscalYearId']",
        "#ddlFiscalYear", "select#ddlFiscalYear",
        "select[name='ddlFiscalYear']",
    ]
    for sel in candidates:
        if page.query_selector(sel):
            return sel
    selects = page.query_selector_all("select")
    if len(selects) == 1:
        return "select"
    raise RuntimeError("Cannot find fiscal year dropdown.")


def _get_current_fiscal_year(
    page, change_fiscal_url: str, logger: logging.Logger
) -> str:
    """Reads currently active fiscal year from portal."""
    page.goto(change_fiscal_url)
    try:
        page.wait_for_selector("text=Change Fiscal Year", timeout=10000)
    except Exception:
        page.wait_for_selector("text=Fiscal Year", timeout=10000)

    selector = _find_fiscal_selector(page)
    return page.eval_on_selector(
        selector,
        "el => el.options[el.selectedIndex]?.text?.trim()"
    )


def _switch_fiscal_year(
    page,
    change_fiscal_url: str,
    target_fiscal: str,
    logger: logging.Logger
) -> None:
    """Switches portal to the required fiscal year."""
    logger.info(
        f"[DOWNLOADER] Switching fiscal year → {target_fiscal}..."
    )
    page.goto(change_fiscal_url)
    try:
        page.wait_for_selector("text=Change Fiscal Year", timeout=100000)
    except Exception:
        page.wait_for_selector("text=Fiscal Year", timeout=100000)

    selector = _find_fiscal_selector(page)
    page.locator(selector).select_option(label=target_fiscal)

    switch_btn = page.locator(
        "button:has-text('Switch to Fiscal'), "
        "input[value='Switch to Fiscal']"
    )
    if switch_btn.count() == 0:
        raise RuntimeError("Cannot find 'Switch to Fiscal' button.")

    switch_btn.click()
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    logger.info(
        f"[DOWNLOADER] ✅ Fiscal year switched to {target_fiscal}."
    )