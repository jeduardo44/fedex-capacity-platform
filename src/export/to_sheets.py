"""Push summary tables to Google Sheets via gspread.

Requires a Google service account JSON key. Set the environment variable
``GSPREAD_SERVICE_ACCOUNT`` to its path (keep the key out of git - it is
covered by .gitignore). Share the target spreadsheet with the service
account's email address.
"""

from __future__ import annotations

import os

import pandas as pd

from src.utils.logger import log


def dataframe_to_sheet(
    df: pd.DataFrame,
    spreadsheet_name: str,
    worksheet_name: str = "Sheet1",
) -> None:
    """Replace the contents of a worksheet with a DataFrame."""
    import gspread  # local import: only needed when actually exporting

    key_path = os.environ.get("GSPREAD_SERVICE_ACCOUNT")
    if not key_path:
        raise EnvironmentError(
            "Set GSPREAD_SERVICE_ACCOUNT to the path of a Google service "
            "account JSON key to export to Google Sheets."
        )

    client = gspread.service_account(filename=key_path)
    spreadsheet = client.open(spreadsheet_name)
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            worksheet_name, rows=len(df) + 1, cols=len(df.columns)
        )

    worksheet.clear()
    worksheet.update(
        [df.columns.tolist()] + df.astype(object).where(df.notna(), "").values.tolist()
    )
    log.info("Pushed {} rows to '{}' / '{}'", len(df), spreadsheet_name, worksheet_name)
