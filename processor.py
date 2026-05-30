# ============================================================
# REPORT PROCESSOR + EMAIL SENDER
# processor.py
# ============================================================

import pandas as pd
import shutil
import logging
import time
import smtplib
import ssl
import configparser

from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


# ============================================================
# STATIC FILTER DATA
# ============================================================

status_exclude = ["CANCELLED", "VOID"]

corporate_exclude_list = [
    "Airport Individual",
    "Demo limited 2",
    "WtiCabs.Com",
    "Aaveg Management Services Pvt Ltd",
    "Aaveg Management Services Pvt Ltd - ETS (997311)",
    "Aaveg Management Services Pvt Ltd - ETS (996412)",
    "Demo limited 3",
    "Make My Trip – B2B2C",
    "Make My Trip – B2B2C (With GST)",
    "Mobisign Services Private Limited",
    "WTi B2C",
    "Wti Fleet Providers Private Limited - 997311",
    "LEASE SALE of DCO Vendors",
    "Trekker Travels Private Limited",
    "Wti Fleet Providers Private Limited-LTR",
    "Wti Fleet Providers Private Limited - Nokia ETS (996412)",
    "Ericsson India Private Limited - LTR 996412",
    "Timken Engineering And Research India - ETS (996412)",
    "Maruti Suzuki India Limited - Bus (997311)",
    "Amazon Smart Commerce Solutions Private Limited - B992",
    "BP Business Solutions India Private Ltd - ETS (996412)",
    "Kohler India Corporation Private Limited - ETS (996412)",
    "Ciena India Private Limited - ETS (996412)",
    "Ciena Communications India Private Limited - ETS (996412)",
    "Sun Life Global Solutions Private Limited - ETS (996412)",
    "Concentrix Daksh Services India Private Limited-Infinity ETS (996412)",
    "Concentrix Daksh Services India Private Limited-SEZ ETS (996412)",
    "BA Continuum India Pvt Ltd SEZ - ETS (996412)",
    "BA Continuum India Pvt Ltd - ETS (996412)",
    "Synechron Technologies Private Limited SEZ - ETS (996412)",
    "KPMG Global Delivery Center Private Limited - ETS (996412)",
    "KPMG Global Services Private Limited - ETS (996412)",
    "Qualcomm India Private Limited - ETS (996412)",
    "iOPEX Technologies Private Limited - ETS (996412)",
    "AGS Health Private Limited - ETS (996412)",
    "International Real Estate Partners (India) Private Limited - ETS (996412)",
    "UBS Business Solutions (India) Private Limited - ETS EON SEZ (996412)",
    "Technocraze Computing Solution Pvt. Ltd. - ETS (996412)",
    "Marken Limited - ETS (996412)",
    "Jaguar Land Rover Technology And Business Services India Pvt Ltd - ETS (996412)",
    "Alten Calsoft Labs (India) Private Limited - ETS (996412)",
    "Indorama Ventures Global Shared Services Private Limited SEZ – ETS (996412)",
    "Cohnreznick Professional Services Private Limited - ETS (996412)",
    "Euro Cab Services Private Limited - ETS (996412)",
    "Teleperformance Global Business Private Limited SEZ - ETS (996601)",
    "Jaguar Land Rover Technology And Business Services India Pvt Ltd - ISD ETS (996412)",
    "Tata Consultancy Services Ltd. - ETS (996412)",
    "BP India Private Limited - ETS (996412)",
    "Tata Consultancy Services Limited SEZ - ETS (996412)",
    "IBM India Pvt Ltd - ETS (996412)",
    "Icertis Solutions Private Limited - ETS (996412)",
    "Vodafone Idea Limited - ETS (996412)",
    "Vikram Thermo India Limited - ETS (996412)",
    "ASG India Operations Private Limited - ETS (996412)",
    "Medtronic Minimed India Private Limited - ETS (996412)",
    "Rehlko Energy India Private Limited - ETS (996412)",
    "Zomato Limited - ETS (996412)",
    "UBS Securities India Pvt. Ltd. - ETS (996412)",
    "PricewaterhouseCoopers Professional Services LLP - ETS (996412)",
    "Azurity Pharmaceuticals India LLP - ETS (996412)",
    "Technip Energies India Limited - ETS (996412)",
    "Brightsun Travels Private Limited - ETS (996412)",
    "Philips Global Business Services LLP SEZ - ETS (996412)",
    "Wipro HR Services India Private Limited SEZ - ETS (996412)",
    "Wipro Limited SEZ - ETS (996412)",
    "TRGRP India Private Limited - ETS (996412)",
    "Vachi Ventures LLP - ETS (996412)",
    "Entrata India Private Limited - ETS (996412)",
    "Johnson Controls (India) Pvt. Ltd. - ETS (996412)",
    "Interglobe Aviation Limited - ETS (996412)",
    "Oji Interpack India Private Limited - ETS (996412)",
    "Vaco Binary Semantics LLP Candor SEZ - ETS (996412)",
    "Span Technology Services Private Limited - ETS (996412)",
    "Quantra Technology Solutions Private Limited - ETS (996412)",
    "Qualcomm India Private Limited SEZ - ETS (996412)",
    "Innover Digital Private Limited - ETS (996412)",
    "Tata Consultancy Services Limited SEZ - ETS (996412) Indore",
    "Capgemini Technology Services India Limited SEZ - ETS (996412)",
    "Quest Global Engineering Services Private Limited SEZ - ETS (996412)",
    "Siemens Limited - ETS (996412)",
    "4AT Consulting LLP - ETS (996412)",
    "Lexmark International (India) Private Limited - ETS (996412)",
    "Knorr-Bremse Technology Center India Pvt Ltd - ETS (996412)",
    "Teleperformance Global Business Private Limited - ETS (996412)",
    "Globe Centrix Associates - ETS (996412)",
    "LINKEDIN TECHNOLOGY INFORMATION PVT. LTD. - ETS (996412)",
    "XL India Business Services Pvt. Ltd SEZ - ETS (996412)",
    "HT Media Ltd. - ETS (996412)",
    "Times Internet Limited - ETS (996412)",
    "UD Trucks India Private Limited - ETS (996412)",
    "Microsoft India (R&D) Pvt Ltd - ETS (996412)",
    "American Express (India) Private Limited - ETS (996412)",
    "Ernst And Young LLP - ETS (996412)",
    "EY Global Delivery Services India LLP - ETS (996412)",
    "Binary Semantics Ltd - ETS (996412)",
    "Vaco Binary Semantics LLP - ETS (996412)",
    "INTERCONTINENTAL HOTELS GROUP ( INDIA) PRIVATE LIMITED - ETS (996412)",
    "Fiserv India Private Limited - ETS (996412)",
    "EYGBS (INDIA) LLP - ETS (996412)",
    "Kellogg Brown & Root Engineering & Construction India Pvt Ltd. - ETS (996412)",
    "Capgemini Technology Services India Limited-RMZ - ETS (996412)",
    "Rostrum Realty Private Limited - ETS (996412)",
    "BMC SOFTWARE INDIA PRIVATE LIMITED - ETS (996412)",
    "Northern Operating Services Private Limited - SEZ ETS (996412)",
    "Valvoline Lubricants & Solutions India Pvt. Ltd. - ETS (996412)",
    "Bahwan CyberTek Pvt. Ltd. - ETS (996412)",
    "UBS Business Solutions (India) Private Limited - ETS Airoli SEZ (996412)",
    "SUN KNOWLEDGE PRIVATE LIMITED - ETS (996412)",
    "Decathlon Sports India Private Limited - ETS (996412)",
    "Protiviti India Member Private Limited - ETS (996412)",
    "Genpact India Pvt. Ltd. - ETS (996412)",
    "Microsoft Corporation India Pvt. Ltd. - ETS (996412)",
    "Midland Credit Management India Private Limited SEZ - ETS (996412)",
    "BCT Consulting Private Limited - ETS (996412)",
    "Technicolor India Shared Services LLP - ETS (996412)",
    "Global Edge Software Limited SEZ - ETS (996412)",
    "Transact Campus India Private Limited - ETS (996412)",
    "Northern Operating Solutions Private Limited SEZ - ETS (996412)",
    "AllState India Pvt. Ltd. -SEZ ETS (996412)",
    "BP Business Solutions India Private Ltd- SEZ - ETS (996412)",
    "Tomtom India Private Limited - ETS (996412)",
    "WU Technology Engineering Services Private Limited - ETS (996412)",
    "Western Union Services India Private Limited - ETS (996412)",
    "IBM India Pvt Ltd SEZ - ETS (996412)",
    "Cotiviti India Pvt. Ltd. - ETS (996412)",
    "F9 Construction Services Private Limited - ETS (996412)",
    "NCheng India Pvt. Ltd. - ETS (996412)",
    "Consilio India Private Limited - ETS (996412)",
    "DataTracks Services Private Limited - ETS (996412)",
    "Brightchamps Tech Private Limited - ETS (996412)",
    "Vantiva India Private Limited - ETS (996412)",
    "Infinite Computer Solutions (India) Limited - ETS (996412)",
    "Omnicom Media Group India Pvt. Ltd. - ETS (996412)",
    "ChargePoint Technologies India Private Limited - ETS (996412)",
    "Whirlpool Asia LLP - ETS (996412)",
    "Ericsson India Private Limited - 996412",
    "Celebi Ground Services Chennai Private Limited - ETS ( 996412 )",
    "Firstsource Solutions Limited SEZ - ETS (996412)",
    "Firstsource Solutions Limited SEZ - ETS (998599)",
    "BP Business Solutions India Private Ltd -  ISD ETS (996412)",
    "Health Prime Services (India) Private Limited SEZ - ETS (996412)",
    "Highspring India LLP Candor SEZ - ETS (996412)",
    "Eternal Limited - ETS (996412)",
    "JoulestoWatts Business Solutions Private Limited - ETS (996412)",
    "Peach Media Private Limited - ETS (996412)",
    "Lear Automotive India Private Limited - ETS (996412)",
    "Highspring India LLP - ETS (996412)",
    "UBS Business Solutions (India) Private Limited - ETS CZ (996412)",
    "Sensormatic India Private Limited - ETS (996412)",
    "Cvent India Private Limited SEZ - ETS (996412)",
    "RNF Technologies Private Limited - ETS (996412)",
    "Lear India Engineering LLP - ETS (996412)",
    "Air India Ltd. - ETS (996412)",
    "Convergys India Services Private Limited - ETS (996412)",
    "Bread Financial Global Solutions India LLP - ETS (996412)",
    "Thermax Babcock & Wilcox Energy Solutions Ltd - ETS (996412)",
    "Gearinc Services India Private Limited - ETS (996412)",
    "Everise (India) BPO Services Private Limited - ETS (996412)",
    "TYCO Safety Product India Private Limited - ETS (996412)",
    "Flexability HR Solutions Private Limited - ETS (996412)",
    "Signify Innovations India Limited - ETS (996412)",
    "Fulfillment Software Private Limited - ETS (996412)",
    "Standard & Poor's South Asia Services Private Limited - ETS (996412)",
    "JoulestoWatts Business Solutions Private Limited - ETS (998599)",
    "New Delhi Television Limited - ETS (996412)",
    "QBML Media Limited - ETS (996412)",
    "Fargo Facilities Management Pvt Ltd - ETS (996412)",
    "SourceHOV India Private Limited - ETS (996412)",
    "CIP FS Global Services India Private Limited- ETS (996412)",
    "KPMG Delivery Network India Private Limited - ETS (996412)",
    "Genpact India Pvt. Ltd. SEZ - ETS (996412)",
    "Marelli (India) Private Limited SEZ - ETS (996412)",
    "Marelli (India) Private Limited - ETS (996412)-Reimbursement",
    "Lamprell India Private Limited - ETS (996412)",
    "Halliburton Development Center India LLP SEZ - ETS (996412)",
    "KPMG Assurance And Consulting Services LLP - ETS (996412)",
    "Amazon Smart Commerce Solutions Private Limited - B990",
    "Zomato Hyperpure Private Limited - ETS (996412)",
    "Keka Technologies Private Limited - ETS (996412)",
    "Qatar Airways Group (Q.C.S.C.) - ETS (996412)",
    "Qatar Airways CDC Private Limited - ETS (996412)",
    "HSBC Software Development (India) Private Limited - ETS (996412)",
    "Citicorp Services India Pvt Ltd SEZ - ETS (996412)",
    "Wti Fleet Providers Private Limited - Nokia ETS (996412)",
    "Fuller Technologies Cement India LLP - ETS (996412)",
    "Citicorp Services India Pvt Ltd - ETS (996412)",
    "Citigroup Global Markets India Private Limited - ETS (996412)",
    "Ciena India Private Limited SEZ - ETS (996412)",
    "Citibank - ETS (996412)",
    "RevStream Solution Private Limited - ETS (996412)",
    "Herbalife International India Private Limited - ETS (996412)",
    "Deloitte & Touche Assurance and Enterprise Risk Services India Private Limited - ETS (996412)",
    "Deloitte Consulting India Private Limited - ETS (996412)",
    "F9 Construction Services Private Limited -ETS (996412)",
    "Consilio India Private Limited -ETS (996412)",
    "CMPMS Global Private Limited - ETS (996412)",
    "Deloitte Tax Services India Private Limited - ETS (996412)",
    "The Hongkong And Shanghai Banking Corporation Ltd - ETS (996412)",
]

linkedin_corporates = [
    "LinkedIn Technology Information Private Limited-BLR",
    "LinkedIn Technology Information Private Limited – GGN",
    "LinkedIn Technology Information Private Limited – MUM",
    "LINKEDIN TECHNOLOGY INFORMATION PVT. LTD. - ETS (996412)",
]

allowed_bookingby = [
    "Naveen S", "ankit.ahuja", "Priya Rautela", "kishan.kumar",
    "Vikas K", "aman.makkar", "parul.verma", "Deepak", "irfan.khan",
    "tarunpreet.dhingra", "kanchan.chauhan", "Yudhveer Singh W04209",
    "Mintu W02122", "Sourabh.Thukral", "Taniya Gusain", "Naman Singh",
    "Kunal.Singh", "raghvendra.singh", "Suhani Goenka", "Ashish.Dagoria",
    "Vikram.Sharma", "Nigam Sharma", "Nitin.Solanki",
]

linkedin_columns = [
    "BookingNo", "Corporate", "Traveller", "CabRequiredOn",
    "Mobile", "Email", "PaymentMode", "Status", "Hub", "CostCode",
]

common_columns = [
    "BookingNo", "BookerName", "Corporate", "Traveller", "CabRequiredOn",
    "Mobile", "Email", "PaymentMode", "BookingBy", "BookingOn", "Status",
    "Hub", "Run", "EmployeeID", "CostCode", "TransNo", "PackageName",
]


# ============================================================
# FOLDER SETUP
# ============================================================

def get_month_folder_name(date: datetime) -> str:
    return date.strftime("%b-%Y")


def setup_folder_structure(
    base_date: datetime,
    config: configparser.ConfigParser
) -> dict:
    root         = Path(config["PATHS"]["root_output_folder"])
    month_folder = root / get_month_folder_name(base_date)
    folders = {
        "month":      month_folder,
        "daily":      month_folder / "Daily Downloads",
        "dump":       month_folder / "Dump Downloads",
        "attachment": month_folder / "Mail Attachment",
    }
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    return folders


# ============================================================
# DAILY / DUMP ROTATION
# ============================================================

def manage_download_folders(
    input_file: Path,
    folders: dict,
    logger: logging.Logger,
) -> None:
    daily = folders["daily"]
    dump  = folders["dump"]

    existing = list(daily.glob("*.xlsx")) + list(daily.glob("*.xls"))
    if existing:
        logger.info(
            f"[PROCESSOR] Moving {len(existing)} file(s) → Dump Downloads"
        )
        for old in existing:
            dest = dump / old.name
            shutil.move(str(old), str(dest))
            logger.info(f"[PROCESSOR]   Moved : {old.name}")
    else:
        logger.info(
            "[PROCESSOR] Daily Downloads empty — nothing to move."
        )

    dest_daily = daily / input_file.name
    shutil.copy2(str(input_file), str(dest_daily))
    logger.info(
        f"[PROCESSOR] Copied to Daily Downloads: {input_file.name}"
    )


# ============================================================
# LOAD & CLEAN DATA
# ============================================================

def load_data(
    input_file: Path,
    logger: logging.Logger
) -> pd.DataFrame:
    logger.info(f"[PROCESSOR] Reading: {input_file.name}")
    df = pd.read_excel(input_file, dtype=str)
    df.columns = df.columns.str.strip()
    logger.info(f"[PROCESSOR] Total rows loaded: {len(df)}")
    
    return df

def clean_data(
    df: pd.DataFrame,
    logger: logging.Logger
) -> pd.DataFrame:

    all_required = set(
        linkedin_columns + common_columns +
        ["Status", "Corporate", "BookingBy", "BookingNo", "CabRequiredOn"]
    )
    missing = all_required - set(df.columns)
    if missing:
        logger.warning(
            f"[PROCESSOR] Missing columns added empty: {sorted(missing)}"
        )
    for col in missing:
        df[col] = ""

    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

    logger.info("[PROCESSOR] Data cleaned successfully.")
    return df


# ============================================================
# REPORT DATE LABEL
# ============================================================

def get_report_label(run_date: datetime, logger: logging.Logger) -> str:
    if run_date.day == 1:
        label = run_date.strftime("%b-%Y")
    else:
        label = run_date.strftime("%d-%b-%Y")
    logger.info(f"[PROCESSOR] Report label: {label}")
    return label


# ============================================================
# LOAD PROCESSED STORE
# ============================================================

def load_store(
    store_path: Path,
    logger: logging.Logger
) -> tuple:
    if store_path.exists():
        processed_df = pd.read_csv(store_path, dtype=str)
        processed_df.columns = processed_df.columns.map(lambda x: str(x).strip())
        if "BookingNo" not in processed_df.columns:
            processed_df["BookingNo"] = ""
        processed_df["BookingNo"] = (
            processed_df["BookingNo"]
            .fillna("").astype(str).str.strip()
        )
        processed_nos = set(processed_df["BookingNo"]) - {""}
        logger.info(
            f"[PROCESSOR] Store loaded: {len(processed_nos)} "
            f"previously processed bookings."
        )
    else:
        processed_nos = set()
        logger.info("[PROCESSOR] No store file — starting fresh.")
    return processed_nos


# ============================================================
# APPLY FILTERS
# ============================================================

def apply_filters(
    df: pd.DataFrame,
    processed_nos: set,
    logger: logging.Logger,
) -> pd.DataFrame:
    df["Status_clean"]      = df["Status"].str.upper().str.strip()
    df["PaymentMode_clean"] = df["PaymentMode"].str.upper().str.strip()
    df["Corporate_clean"]   = df["Corporate"].str.strip()
    df["BookingBy_clean"]   = df["BookingBy"].str.strip()
    df["BookingNo_clean"]   = df["BookingNo"].str.strip()

    start = len(df)

    df = df[~df["Status_clean"].isin(status_exclude)].copy()
    a1 = len(df)
    logger.info(
        f"[PROCESSOR] After Status filter    : {a1} rows "
        f"(removed {start - a1})"
    )

    df = df[~df["Corporate_clean"].isin(corporate_exclude_list)].copy()
    a2 = len(df)
    logger.info(
        f"[PROCESSOR] After Corporate filter : {a2} rows "
        f"(removed {a1 - a2})"
    )

    df = df[~df["BookingNo_clean"].isin(processed_nos)].copy()
    a3 = len(df)
    logger.info(
        f"[PROCESSOR] After Dedup filter     : {a3} rows "
        f"(removed {a2 - a3} already processed)"
    )

    logger.info(f"[PROCESSOR] Final rows to process: {a3}")
    return df


# ============================================================
# SPLIT DATA
# ============================================================

def split_data(
    df: pd.DataFrame,
    logger: logging.Logger
) -> tuple:
    linkedin_df = df[
        df["Corporate_clean"].isin(linkedin_corporates)
    ][linkedin_columns].copy()
    linkedin_df["Correct Cost Code"] = ""

    nonbtc_df = df[
        (df["PaymentMode_clean"] != "BTC") &
        (df["BookingBy_clean"].isin(allowed_bookingby))
    ][common_columns].copy()

    btc_df = df[
        (df["PaymentMode_clean"] == "BTC") &
        (df["BookingBy_clean"].isin(allowed_bookingby))
    ][common_columns].copy()

    excluded = df[
        (~df["BookingBy_clean"].isin(allowed_bookingby)) &
        (~df["Corporate_clean"].isin(linkedin_corporates))
    ]

    logger.info(f"[PROCESSOR] LinkedIn rows         : {len(linkedin_df)}")
    logger.info(f"[PROCESSOR] All Corp Non-BTC rows : {len(nonbtc_df)}")
    logger.info(f"[PROCESSOR] All Corp BTC rows     : {len(btc_df)}")

    if len(excluded) > 0:
        logger.warning(
            f"[PROCESSOR] {len(excluded)} rows excluded — "
            f"BookingBy not in allowed list & not LinkedIn."
        )
    return linkedin_df, nonbtc_df, btc_df


# ============================================================
# WRITE OUTPUT FILES
# ============================================================

def write_output_files(
    linkedin_df: pd.DataFrame,
    nonbtc_df: pd.DataFrame,
    btc_df: pd.DataFrame,
    folders: dict,
    report_label: str,
    logger: logging.Logger,
) -> tuple:
    att = folders["attachment"]

    # File 1: LinkedIn
    linkedin_file = att / f"LinkedIn_Report_{report_label}.xlsx"
    with pd.ExcelWriter(linkedin_file, engine="openpyxl") as w:
        linkedin_df.to_excel(w, sheet_name="LinkedIn Client", index=False)
    logger.info(f"[PROCESSOR] LinkedIn file : {linkedin_file.name}")

    # File 2: BTC
    btc_file = att / f"BTC_Report_{report_label}.xlsx"
    with pd.ExcelWriter(btc_file, engine="openpyxl") as w:
        btc_df.to_excel(
            w,
            sheet_name=f"All Corp BTC {report_label}",
            index=False
        )
    logger.info(f"[PROCESSOR] BTC file     : {btc_file.name}")

    # File 3: Non-BTC
    nonbtc_file = att / f"Non_BTC_Report_{report_label}.xlsx"
    with pd.ExcelWriter(nonbtc_file, engine="openpyxl") as w:
        nonbtc_df.to_excel(
            w,
            sheet_name=f"All Corp Non BTC {report_label}",
            index=False
        )
    logger.info(f"[PROCESSOR] Non-BTC file : {nonbtc_file.name}")

    return linkedin_file, btc_file, nonbtc_file


# ============================================================
# UPDATE STORE
# ============================================================

def update_store(
    df: pd.DataFrame, # New Bookings Value
    store_path: Path, # File Path where Processed Booking No Stored
    processed_df: pd.DataFrame, # Processed - Inital Dump Dataframe
    logger: logging.Logger,
) -> None:
    new_nos = pd.DataFrame({"BookingNo": df["BookingNo_clean"]})
    new_nos = new_nos[new_nos["BookingNo"] != ""].drop_duplicates()

    # Keep only BookingNo column from processed_df
    processed_nos = (
        processed_df.loc[processed_df["BookingNo"] != "", ["BookingNo"]]
        .drop_duplicates()
    )
    processed_nos.to_csv(store_path, index=False)

    logger.info(
        f"[PROCESSOR] Store updated: +{len(new_nos)} new | "
        f"Total: {len(processed_nos)}"
    )


# ============================================================
# HTML EMAIL BUILDER
# ============================================================

def build_html_body(
    report_type: str,
    report_label: str,
    attachment_name: str,
) -> str:
    generated_on = datetime.today().strftime("%d-%b-%Y %H:%M")

    if report_type == "LinkedIn":
        report_title = f"LinkedIn Booking Report: {report_label}"
        body_content = """
            <strong>Dear Team,</strong><br><br>
            Please find attached the <strong>LinkedIn Booking Report</strong>.<br><br>
            Request you to review the <strong>Cost Code</strong> mentioned
            in the report and make the necessary corrections for
            billing purposes.<br><br>
            Kindly update the same at the earliest to avoid any
            billing discrepancies.
        """

    elif report_type == "BTC":
        report_title = f"BTC Booking Report: {report_label}"
        body_content = """
            <strong>Dear Team,</strong><br><br>
            Please find attached the <strong>BTC Booking Report</strong>.<br><br>
            Request you to review the <strong>Payment Mode</strong>
            details and make the necessary corrections for
            billing purposes.<br><br>
            Kindly ensure the updates are completed at the earliest
            to avoid billing issues.
        """

    else:  # Non-BTC
        report_title = f"Non-BTC Booking Report: {report_label}"
        body_content = """
            <strong>Dear Team,</strong><br><br>
            Please find attached the <strong>Non-BTC Booking Report</strong>.<br><br>
            Request you to review the <strong>Payment Mode</strong>
            details and make the necessary corrections for
            billing purposes.<br><br>
            Kindly ensure the updates are completed at the earliest
            to avoid billing issues.
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #e5e5e5;
            font-family: Segoe UI, Arial, sans-serif;
            overflow-x: hidden;
        }}
        .container {{
            width: 875px;
            margin: 0 auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <center>
            <table width="100%" bgcolor="#e5e5e5"
                   cellpadding="0" cellspacing="0" border="0">
                <tr>
                    <td align="center" style="padding:30px;">

                        <table width="100%" cellpadding="0"
                               cellspacing="0" border="0"
                               style="background-color:#ffffff;
                                      border-top:6px solid #00085D;
                                      border-radius:6px;">

                            <!-- Header -->
                            <tr>
                                <td style="padding:25px 30px 15px 30px;">
                                    <table width="100%" cellpadding="0"
                                           cellspacing="0" border="0">
                                        <tr>
                                            <td style="font-size:16px;
                                                       color:#333333;
                                                       font-weight:bold;
                                                       padding-bottom:5px;">
                                                {report_title}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="font-size:12px;
                                                       color:#666666;">
                                                Generated on:
                                                <strong>
                                                    {generated_on}
                                                </strong>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                            <!-- Body Content -->
                            <tr>
                                <td style="padding:10px 30px 20px 30px;
                                           font-size:13px;
                                           color:#333333;
                                           line-height:1.8;">
                                    {body_content}
                                </td>
                            </tr>

                            <!-- Attachment Note -->
                            <!-- Signature -->
                            <tr>
                                <td style="padding:15px 30px 25px 30px;
                                           background-color:#f9f9f9;
                                           border-top:1px solid #dddddd;">
                                    <table width="100%" cellpadding="0"
                                           cellspacing="0" border="0">
                                        <tr>
                                            <td style="vertical-align:top;">
                                                <table cellpadding="0"
                                                       cellspacing="0"
                                                       border="0">
                                                    <tr>
                                                        <td style="font-size:12px;
                                                                   color:#444444;
                                                                   padding-bottom:5px;">
                                                            <strong>
                                                                Thanks &amp; Regards,
                                                            </strong>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="font-size:13px;
                                                                   color:#00085D;
                                                                   font-weight:bold;
                                                                   padding-bottom:5px;">
                                                            Command Centre
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="font-size:12px;
                                                                   color:#666666;">
                                                            BI Team
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                            <td align="right"
                                                style="vertical-align:top;">
                                                <img src="https://dgdlm6ddvctpd.cloudfront.net/bannerimages/wtiintelligentmobility.png"
                                                     alt="WTi Cabs Logo"
                                                     width="100"
                                                     style="display:block;
                                                            border:0;">
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>

                        </table>
                    </td>
                </tr>
            </table>
        </center>
    </div>
</body>
</html>"""
    return html


# ============================================================
# EMAIL HELPERS
# ============================================================

def parse_recipients(raw: str) -> list:
    if not raw or not raw.strip():
        return []
    return [e.strip() for e in raw.split(",") if e.strip()]


def build_email_message(
    sender_email: str,
    sender_name: str,
    to_list: list,
    cc_list: list,
    bcc_list: list,
    subject: str,
    html_body: str,
    attachment_path: Path,
) -> MIMEMultipart:
    msg            = MIMEMultipart("mixed")
    msg["From"]    = f"{sender_name} <{sender_email}>"
    msg["To"]      = ", ".join(to_list)
    msg["Subject"] = subject
    if cc_list:
        msg["Cc"]  = ", ".join(cc_list)

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with open(attachment_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{attachment_path.name}"',
    )
    msg.attach(part)
    return msg


def send_email(
    msg: MIMEMultipart,
    to_list: list,
    cc_list: list,
    bcc_list: list,
    config: configparser.ConfigParser,
    logger: logging.Logger,
    report_type: str,
) -> bool:
    smtp_host    = config["SMTP"]["smtp_host"].strip()
    smtp_port    = int(config["SMTP"]["smtp_port"].strip())
    use_tls      = config["SMTP"].getboolean("use_tls")
    sender_email = config["SMTP"]["sender_email"].strip()
    sender_pass  = config["SMTP"]["sender_password"].strip()
    max_retries  = int(config["EMAIL_SETTINGS"]["retry_attempts"].strip())
    retry_delay  = int(config["EMAIL_SETTINGS"]["retry_delay_sec"].strip())
    all_recv     = to_list + cc_list + bcc_list

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                f"[EMAIL][{report_type}] Attempt {attempt}/{max_retries} "
                f"→ {smtp_host}:{smtp_port}"
            )
            if use_tls:
                ctx = ssl.create_default_context()
                with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
                    s.ehlo()
                    s.starttls(context=ctx)
                    s.ehlo()
                    s.login(sender_email, sender_pass)
                    s.sendmail(sender_email, all_recv, msg.as_string())
            else:
                ctx = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    smtp_host, smtp_port, context=ctx, timeout=30
                ) as s:
                    s.login(sender_email, sender_pass)
                    s.sendmail(sender_email, all_recv, msg.as_string())

            logger.info(
                f"[EMAIL][{report_type}] ✅ Sent successfully! "
                f"To:{to_list} CC:{cc_list} BCC:{bcc_list}"
            )
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(
                f"[EMAIL][{report_type}] ❌ Auth failed — "
                f"check email/password in config.ini"
            )
            return False

        except Exception as e:
            logger.warning(
                f"[EMAIL][{report_type}] ⚠️  Attempt {attempt} failed: {e}"
            )
            if attempt < max_retries:
                logger.info(f"[EMAIL] Retrying in {retry_delay}s...")
                time.sleep(retry_delay)

    logger.error(
        f"[EMAIL][{report_type}] ❌ All {max_retries} attempts failed."
    )
    return False


# ============================================================
# EMAIL ORCHESTRATOR
# ============================================================

def send_report_emails(
    linkedin_file: Path,
    btc_file: Path,
    nonbtc_file: Path,
    linkedin_df: pd.DataFrame,
    nonbtc_df: pd.DataFrame,
    btc_df: pd.DataFrame,
    report_label: str,
    config: configparser.ConfigParser,
    logger: logging.Logger,
) -> None:
    send_if_empty = config["EMAIL_SETTINGS"].getboolean("send_if_empty")

    # ── EMAIL 1: LinkedIn ─────────────────────────────────────
    logger.info("[EMAIL] " + "-" * 50)
    logger.info("[EMAIL][LinkedIn] Preparing...")

    if linkedin_df.empty and not send_if_empty:
        logger.warning(
            "[EMAIL][LinkedIn] ⚠️  0 rows — email SKIPPED."
        )
    else:
        to   = parse_recipients(config["EMAIL_LINKEDIN"]["to"])
        cc   = parse_recipients(config["EMAIL_LINKEDIN"].get("cc", ""))
        bcc  = parse_recipients(config["EMAIL_LINKEDIN"].get("bcc", ""))
        subj = config["EMAIL_LINKEDIN"]["subject"].replace(
            "{date}", report_label
        )
        if not to:
            logger.error("[EMAIL][LinkedIn] No TO recipients — skipped.")
        else:
            html = build_html_body(
                "LinkedIn", report_label, linkedin_file.name
            )
            msg = build_email_message(
                config["SMTP"]["sender_email"].strip(),
                config["SMTP"]["sender_name"].strip(),
                to, cc, bcc, subj, html, linkedin_file,
            )
            send_email(msg, to, cc, bcc, config, logger, "LinkedIn")

    # ── EMAIL 2: BTC ──────────────────────────────────────────
    logger.info("[EMAIL] " + "-" * 50)
    logger.info("[EMAIL][BTC] Preparing...")

    if btc_df.empty and not send_if_empty:
        logger.warning(
            "[EMAIL][BTC] ⚠️  0 rows — email SKIPPED."
        )
    else:
        to   = parse_recipients(config["EMAIL_BTC"]["to"])
        cc   = parse_recipients(config["EMAIL_BTC"].get("cc", ""))
        bcc  = parse_recipients(config["EMAIL_BTC"].get("bcc", ""))
        subj = config["EMAIL_BTC"]["subject"].replace(
            "{date}", report_label
        )
        if not to:
            logger.error("[EMAIL][BTC] No TO recipients — skipped.")
        else:
            html = build_html_body(
                "BTC", report_label, btc_file.name
            )
            msg = build_email_message(
                config["SMTP"]["sender_email"].strip(),
                config["SMTP"]["sender_name"].strip(),
                to, cc, bcc, subj, html, btc_file,
            )
            send_email(msg, to, cc, bcc, config, logger, "BTC")

    # ── EMAIL 3: Non-BTC ──────────────────────────────────────
    logger.info("[EMAIL] " + "-" * 50)
    logger.info("[EMAIL][Non-BTC] Preparing...")

    if nonbtc_df.empty and not send_if_empty:
        logger.warning(
            "[EMAIL][Non-BTC] ⚠️  0 rows — email SKIPPED."
        )
    else:
        to   = parse_recipients(config["EMAIL_NONBTC"]["to"])
        cc   = parse_recipients(config["EMAIL_NONBTC"].get("cc", ""))
        bcc  = parse_recipients(config["EMAIL_NONBTC"].get("bcc", ""))
        subj = config["EMAIL_NONBTC"]["subject"].replace(
            "{date}", report_label
        )
        if not to:
            logger.error("[EMAIL][Non-BTC] No TO recipients — skipped.")
        else:
            html = build_html_body(
                "Non-BTC", report_label, nonbtc_file.name
            )
            msg = build_email_message(
                config["SMTP"]["sender_email"].strip(),
                config["SMTP"]["sender_name"].strip(),
                to, cc, bcc, subj, html, nonbtc_file,
            )
            send_email(msg, to, cc, bcc, config, logger, "Non-BTC")

# ============================================================
# MAIN PROCESSOR ENTRY POINT
# ============================================================

def run_processor(
    config: configparser.ConfigParser,
    logger: logging.Logger,
    downloaded_file_path: str,
) -> bool:
    try:
        run_date   = datetime.today()
        input_file = Path(downloaded_file_path)

        if not input_file.exists():
            logger.error(
                f"[PROCESSOR] Input file not found: {input_file}"
            )
            return False

        folders      = setup_folder_structure(run_date, config)
        store_path   = folders["month"] / config["PATHS"]["store_file_name"]
        report_label = get_report_label(run_date, logger)

        manage_download_folders(input_file, folders, logger)

        dump_df = load_data(input_file, logger)
        
        df = clean_data(dump_df, logger)

        processed_nos = load_store(store_path, logger)

        df_filtered = apply_filters(df, processed_nos, logger)

        if df_filtered.empty:
            logger.warning(
                "[PROCESSOR] No new bookings — writing empty files."
            )
            linkedin_df = pd.DataFrame(columns=linkedin_columns)
            nonbtc_df   = pd.DataFrame(columns=common_columns)
            btc_df      = pd.DataFrame(columns=common_columns)
        else:
            linkedin_df, nonbtc_df, btc_df = split_data(
                df_filtered, logger
            )

        # Write 3 separate output files
        linkedin_file, btc_file, nonbtc_file = write_output_files(
            linkedin_df, nonbtc_df, btc_df,
            folders, report_label, logger
        )

        if not df_filtered.empty:
            update_store(
                df_filtered, store_path, dump_df, logger
            )

        # Send 3 separate emails
        send_report_emails(
            linkedin_file, btc_file, nonbtc_file,
            linkedin_df, nonbtc_df, btc_df,
            report_label, config, logger
        )

        return True

    except Exception as e:
        logger.exception(f"[PROCESSOR] ❌ Unexpected error: {e}")
        return False