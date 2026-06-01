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

    Date range rule (MONTH TRANSITION SAFE):
      - Normal days (2nd to last day of month):
          from = 1st of current month
          to   = last day of current month

      - On 1st of month (SPECIAL CASE):
          Run 1: Download PREVIOUS month complete data
                 (catches any late bookings missed
                  after last download of prev month)
          Run 2: Download CURRENT month data
                 from 1st to last of current month

    Returns:
        list of tuples: [(success, file_path, is_full_month), ...]
        Always returns a list — on 1st of month returns 2 items.
    """

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

    today = datetime.now().date()

    # ── Build download tasks ───────────────────────────────
    tasks = []

    if today.day == 1:
        # ── TASK 1: Previous month complete data ──────────
        # Go back to last day of previous month
        prev_last_day   = today.replace(day=1) - __import__(
            'datetime'
        ).timedelta(days=1)
        prev_first_day  = prev_last_day.replace(day=1)
        prev_last_day_n = calendar.monthrange(
            prev_last_day.year, prev_last_day.month
        )[1]
        prev_to         = prev_last_day.replace(day=prev_last_day_n)

        prev_month_label         = prev_first_day.strftime("%B_%Y")
        prev_month_label_display = prev_first_day.strftime("%B %Y")
        prev_filename = (
            f"Bookings_Data_{prev_month_label}"
            f"_(Complete {prev_month_label_display}).xlsx"
        )

        tasks.append({
            "from_date"    : prev_first_day,
            "to_date"      : prev_to,
            "filename"     : prev_filename,
            "is_full_month": True,
            "label"        : f"PREVIOUS MONTH ({prev_month_label_display})",
        })

        # ── TASK 2: Current month data ────────────────────
        curr_last_day_n = calendar.monthrange(today.year, today.month)[1]
        curr_to         = today.replace(day=curr_last_day_n)
        curr_month_label         = today.strftime("%B_%Y")
        curr_month_label_display = today.strftime("%B %Y")
        curr_filename = (
            f"Bookings_Data_{curr_month_label}"
            f"_(Complete {curr_month_label_display}).xlsx"
        )

        tasks.append({
            "from_date"    : today,
            "to_date"      : curr_to,
            "filename"     : curr_filename,
            "is_full_month": True,
            "label"        : f"CURRENT MONTH ({curr_month_label_display})",
        })

    else:
        # ── Normal day: just current month ────────────────
        from_date       = today.replace(day=1)
        last_day_n      = calendar.monthrange(today.year, today.month)[1]
        to_date         = today.replace(day=last_day_n)
        month_label         = from_date.strftime("%B_%Y")
        month_label_display = from_date.strftime("%B %Y")
        filename = (
            f"Bookings_Data_{month_label}"
            f"_(Complete {month_label_display}).xlsx"
        )

        tasks.append({
            "from_date"    : from_date,
            "to_date"      : to_date,
            "filename"     : filename,
            "is_full_month": True,
            "label"        : f"CURRENT MONTH ({month_label_display})",
        })

    # ── Execute all tasks in ONE browser session ───────────
    results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(accept_downloads=True)
            page    = context.new_page()

            # LOGIN ONCE
            logger.info("[DOWNLOADER] Logging in to WISX portal...")
            page.goto(login_url)
            page.fill("#Email",    user_id)
            page.click("#Password")
            page.fill("#Password", password)
            page.locator(
                "input[type='submit'][value='Log in']"
            ).click()
            page.wait_for_load_state("networkidle")
            logger.info("[DOWNLOADER] ✅ Login successful!")

            for task_idx, task in enumerate(tasks, start=1):
                logger.info("-" * 60)
                logger.info(
                    f"[DOWNLOADER] Task {task_idx}/{len(tasks)}: "
                    f"{task['label']}"
                )
                logger.info(
                    f"[DOWNLOADER] Range    : "
                    f"{task['from_date'].strftime('%d-%m-%Y')} → "
                    f"{task['to_date'].strftime('%d-%m-%Y')}"
                )
                logger.info(
                    f"[DOWNLOADER] Filename : {task['filename']}"
                )

                file_path = os.path.join(
                    download_dir, task["filename"]
                )

                # FISCAL CHECK PER TASK
                current_fiscal = _get_current_fiscal_year(
                    page, change_fiscal_url, logger
                )
                target_fiscal = _get_fiscal_year_for_date(
                    task["from_date"]
                )

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
                        "[DOWNLOADER] ✅ Fiscal year correct."
                    )

                # NAVIGATE & DOWNLOAD
                logger.info(
                    "[DOWNLOADER] Navigating to report page..."
                )
                page.goto(report_url)
                page.wait_for_selector("#FromDate")
                page.select_option("#BranchID", value=branch_id)

                page.eval_on_selector(
                    "#FromDate",
                    "el => el.removeAttribute('readonly')"
                )
                page.eval_on_selector(
                    "#ToDate",
                    "el => el.removeAttribute('readonly')"
                )

                _select_date(
                    page, "#FromDate",
                    datetime(
                        task["from_date"].year,
                        task["from_date"].month,
                        task["from_date"].day,
                    )
                )
                _select_date(
                    page, "#ToDate",
                    datetime(
                        task["to_date"].year,
                        task["to_date"].month,
                        task["to_date"].day,
                    )
                )

                logger.info("[DOWNLOADER] Triggering file download...")
                with page.expect_download(timeout=0) as dl:
                    page.click(
                        "input[type='submit'].btn.btn-success",
                        no_wait_after=True,
                    )

                download = dl.value
                download.save_as(file_path)
                logger.info(
                    f"[DOWNLOADER] ✅ Downloaded: {task['filename']}"
                )

                results.append({
                    "success"      : True,
                    "file_path"    : file_path,
                    "is_full_month": task["is_full_month"],
                    "file_date"    : task["from_date"].strftime("%Y-%m-%d"),
                })

            # LOGOUT ONCE
            logger.info("[DOWNLOADER] Logging out...")
            page.goto(logout_url)
            page.wait_for_load_state("networkidle")
            logger.info("[DOWNLOADER] ✅ Logged out.")

            page.close()
            context.close()
            browser.close()

    except Exception as e:
        logger.exception(f"[DOWNLOADER] ❌ Download failed: {e}")
        # Return failure for remaining tasks
        tasks_done = len(results)
        for t in tasks[tasks_done:]:
            results.append({
                "success"      : False,
                "file_path"    : "",
                "is_full_month": True,
                "file_date"    : t["from_date"].strftime("%Y-%m-%d"),
            })

    return results


# ── All private helpers remain IDENTICAL ──────────────────

def _select_date(page, selector: str, target_date: datetime):
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
        elif datetime.strptime(
            current_month_year, "%B %Y"
        ) > datetime(target_date.year, target_date.month, 1):
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
    if target_date.month >= 4:
        return f"{target_date.year}-{target_date.year + 1}"
    return f"{target_date.year - 1}-{target_date.year}"


def _find_fiscal_selector(page) -> str:
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
    page.goto(change_fiscal_url)
    try:
        page.wait_for_selector(
            "text=Change Fiscal Year", timeout=10000
        )
    except Exception:
        page.wait_for_selector(
            "text=Fiscal Year", timeout=10000
        )
    selector = _find_fiscal_selector(page)
    return page.eval_on_selector(
        selector,
        "el => el.options[el.selectedIndex]?.text?.trim()"
    )


def _switch_fiscal_year(
    page, change_fiscal_url: str,
    target_fiscal: str, logger: logging.Logger
) -> None:
    logger.info(
        f"[DOWNLOADER] Switching fiscal → {target_fiscal}..."
    )
    page.goto(change_fiscal_url)
    try:
        page.wait_for_selector(
            "text=Change Fiscal Year", timeout=100000
        )
    except Exception:
        page.wait_for_selector(
            "text=Fiscal Year", timeout=100000
        )
    selector = _find_fiscal_selector(page)
    page.locator(selector).select_option(label=target_fiscal)
    switch_btn = page.locator(
        "button:has-text('Switch to Fiscal'), "
        "input[value='Switch to Fiscal']"
    )
    if switch_btn.count() == 0:
        raise RuntimeError(
            "Cannot find 'Switch to Fiscal' button."
        )
    switch_btn.click()
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    logger.info(
        f"[DOWNLOADER] ✅ Fiscal switched to {target_fiscal}."
    )
