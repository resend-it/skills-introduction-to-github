"""Financial tracker automation for dry cleaning business.

This script collects transaction data from a CSV file or Google Sheets,
classifies transactions into business categories, computes financial summaries,
and updates Google Sheets worksheets (Summary and Charts_Data) while generating
matplotlib charts for quick analytics. The script can be scheduled to run daily.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

try:
    import gspread
except ImportError:  # pragma: no cover - optional dependency in local mode
    gspread = None  # type: ignore

try:
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover - matplotlib should be installed
    raise RuntimeError("matplotlib is required to run this script") from exc

try:
    import schedule
except ImportError:  # pragma: no cover - schedule only required for cron-like loop
    schedule = None  # type: ignore


LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


DEFAULT_CATEGORY_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "Revenue": ("sale", "pickup", "delivery", "restoration", "revenue"),
    "COGS": ("detergent", "supplies", "hangers", "plastic", "solvent"),
    "Operating Expense": (
        "rent",
        "utility",
        "electric",
        "water",
        "maintenance",
        "marketing",
    ),
    "Payroll": ("payroll", "wage", "salary", "paycheck"),
    "Debt": ("loan", "debt", "interest"),
    "Owner Draw": ("owner draw", "distribution", "draw"),
}


@dataclass
class TrackerConfig:
    """Configuration for financial tracker."""

    csv_path: str = "data/daily_transactions.csv"
    use_google_sheet: bool = False
    google_credentials_json: Optional[str] = None
    spreadsheet_name: Optional[str] = None
    raw_sheet_name: str = "Raw_Transactions"
    summary_sheet_name: str = "Summary"
    charts_sheet_name: str = "Charts_Data"
    chart_output_dir: str = "charts"
    schedule_time: str = "06:00"  # 24-hour format
    category_keywords: Dict[str, Tuple[str, ...]] = field(
        default_factory=lambda: dict(DEFAULT_CATEGORY_KEYWORDS)
    )


class FinancialTracker:
    """Main entry point for synchronising financial data and summaries."""

    def __init__(self, config: TrackerConfig) -> None:
        self.config = config
        self.client = None
        if config.use_google_sheet:
            self.client = self._connect_to_google_sheets()
        os.makedirs(os.path.dirname(self.config.csv_path), exist_ok=True)
        os.makedirs(self.config.chart_output_dir, exist_ok=True)

    def _connect_to_google_sheets(self):
        if not gspread:
            raise RuntimeError(
                "gspread is not installed. Install it or disable Google Sheets integration."
            )
        if not self.config.google_credentials_json:
            raise ValueError("Google credentials JSON path is required for Google Sheets.")
        logger.info("Connecting to Google Sheets spreadsheet: %s", self.config.spreadsheet_name)
        credentials = gspread.service_account(filename=self.config.google_credentials_json)
        return credentials

    # ------------------------- Data Retrieval ---------------------------------
    def fetch_transactions(self) -> pd.DataFrame:
        """Fetch transactions from CSV or Google Sheet."""
        if self.config.use_google_sheet:
            return self._fetch_from_google_sheet()
        logger.info("Loading transactions from CSV: %s", self.config.csv_path)
        if not os.path.exists(self.config.csv_path):
            logger.warning(
                "CSV %s not found. Returning empty DataFrame; ensure the file exists.",
                self.config.csv_path,
            )
            return pd.DataFrame(
                columns=["Date", "Type", "Description", "Amount", "Category"]
            )
        df = pd.read_csv(self.config.csv_path)
        return self._prepare_transactions(df)

    def _fetch_from_google_sheet(self) -> pd.DataFrame:
        assert self.client is not None, "Google Sheets client not initialised"
        spreadsheet = self.client.open(self.config.spreadsheet_name)
        worksheet = spreadsheet.worksheet(self.config.raw_sheet_name)
        records = worksheet.get_all_records()
        df = pd.DataFrame.from_records(records)
        return self._prepare_transactions(df)

    # ----------------------- Data Preparation ---------------------------------
    def _prepare_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            logger.warning("Transaction DataFrame is empty after load.")
            return df
        logger.debug("Preparing transactions DataFrame with %d rows", len(df))
        df = df.copy()
        if "Date" not in df.columns:
            raise ValueError("Transactions must include a 'Date' column.")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        if "Amount" not in df.columns:
            raise ValueError("Transactions must include an 'Amount' column.")
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
        df = df.dropna(subset=["Amount"])
        if "Description" not in df.columns:
            df["Description"] = ""
        df["Description"] = df["Description"].fillna("")
        if "Category" not in df.columns:
            df["Category"] = df.apply(self._classify_transaction, axis=1)
        else:
            missing_category_mask = df["Category"].isna() | (df["Category"] == "")
            df.loc[missing_category_mask, "Category"] = df[missing_category_mask].apply(
                self._classify_transaction, axis=1
            )
        return df

    def _classify_transaction(self, row: pd.Series) -> str:
        description = str(row.get("Description", "")).lower()
        txn_type = str(row.get("Type", "")).lower()
        amount = row.get("Amount", 0)
        if txn_type in ("revenue", "sale", "income") or amount > 0:
            default_category = "Revenue"
        else:
            default_category = "Operating Expense"
        for category, keywords in self.config.category_keywords.items():
            if any(keyword in description for keyword in keywords):
                return category
        return default_category

    # ---------------------- Summary Calculations ------------------------------
    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        if df.empty:
            logger.warning("No transactions to compute metrics.")
            return {}

        df = df.copy()
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)

        revenue_df = df[df["Category"] == "Revenue"]
        expense_df = df[df["Category"] != "Revenue"]
        cogs_df = df[df["Category"] == "COGS"]
        operating_df = df[df["Category"].isin(["Operating Expense", "Rent", "Utilities"])]

        daily_revenue = revenue_df["Amount"].resample("D").sum().fillna(0)
        weekly_revenue = revenue_df["Amount"].resample("W-SUN").sum().fillna(0)
        weekly_expenses = expense_df["Amount"].resample("W-SUN").sum().fillna(0)
        weekly_cogs = cogs_df["Amount"].resample("W-SUN").sum().fillna(0)
        weekly_gross_profit = weekly_revenue - weekly_cogs

        monthly_gross_profit = revenue_df["Amount"].resample("MS").sum() - cogs_df[
            "Amount"
        ].resample("MS").sum()
        monthly_operating_expense = operating_df["Amount"].resample("MS").sum().fillna(0)
        monthly_net_profit = monthly_gross_profit.fillna(0) - monthly_operating_expense

        expense_breakdown = expense_df.groupby("Category")["Amount"].sum().sort_values(
            ascending=False
        )

        return {
            "daily_revenue": daily_revenue,
            "weekly_revenue": weekly_revenue,
            "weekly_expenses": weekly_expenses,
            "weekly_gross_profit": weekly_gross_profit,
            "monthly_net_profit": monthly_net_profit.fillna(0),
            "expense_breakdown": expense_breakdown,
        }

    # ---------------------- Sheet & CSV Updates -------------------------------
    def append_summary(self, metrics: Dict[str, pd.DataFrame]) -> None:
        if not metrics:
            logger.warning("No metrics to append to summary.")
            return
        today = datetime.today().date()
        weekly_revenue = metrics["weekly_revenue"].iloc[-1] if not metrics["weekly_revenue"].empty else 0
        weekly_expenses = metrics["weekly_expenses"].iloc[-1] if not metrics["weekly_expenses"].empty else 0
        weekly_gross_profit = (
            metrics["weekly_gross_profit"].iloc[-1] if not metrics["weekly_gross_profit"].empty else 0
        )
        monthly_net_profit = (
            metrics["monthly_net_profit"].iloc[-1] if not metrics["monthly_net_profit"].empty else 0
        )
        daily_revenue = metrics["daily_revenue"].iloc[-1] if not metrics["daily_revenue"].empty else 0

        summary_row = [
            str(today),
            float(daily_revenue),
            float(weekly_revenue),
            float(weekly_expenses),
            float(weekly_gross_profit),
            float(monthly_net_profit),
        ]
        logger.info(
            "Summary for %s - Daily Revenue: %.2f | Weekly Revenue: %.2f | Weekly Expenses: %.2f",
            today,
            summary_row[1],
            summary_row[2],
            summary_row[3],
        )

        if self.config.use_google_sheet:
            self._append_summary_google_sheet(summary_row)
        else:
            self._append_summary_csv(summary_row)

    def _append_summary_google_sheet(self, summary_row: List) -> None:
        assert self.client is not None
        spreadsheet = self.client.open(self.config.spreadsheet_name)
        worksheet = spreadsheet.worksheet(self.config.summary_sheet_name)
        worksheet.append_row(summary_row, value_input_option="USER_ENTERED")
        logger.info("Appended summary row to Google Sheet '%s'.", self.config.summary_sheet_name)

    def _append_summary_csv(self, summary_row: List) -> None:
        summary_path = os.path.join(os.path.dirname(self.config.csv_path), "summary.csv")
        columns = [
            "Date",
            "Daily Revenue",
            "Weekly Revenue",
            "Weekly Expenses",
            "Weekly Gross Profit",
            "Monthly Net Profit",
        ]
        df = pd.DataFrame([summary_row], columns=columns)
        if os.path.exists(summary_path):
            df_existing = pd.read_csv(summary_path)
            df_all = pd.concat([df_existing, df], ignore_index=True)
            df_all.drop_duplicates(subset=["Date"], keep="last", inplace=True)
            df_all.to_csv(summary_path, index=False)
        else:
            df.to_csv(summary_path, index=False)
        logger.info("Summary data updated at %s", summary_path)

    def update_charts_data(self, metrics: Dict[str, pd.DataFrame]) -> None:
        if not metrics:
            return
        weekly_revenue = metrics["weekly_revenue"].reset_index()
        weekly_revenue.columns = ["Week", "Revenue"]
        expense_breakdown = metrics["expense_breakdown"].reset_index()
        expense_breakdown.columns = ["Category", "Amount"]

        if self.config.use_google_sheet:
            assert self.client is not None
            spreadsheet = self.client.open(self.config.spreadsheet_name)
            worksheet = spreadsheet.worksheet(self.config.charts_sheet_name)
            worksheet.clear()
            worksheet.update([weekly_revenue.columns.values.tolist()] + weekly_revenue.values.tolist())
            worksheet.append_row([])
            worksheet.append_row(expense_breakdown.columns.values.tolist())
            worksheet.update(
                f"A{len(weekly_revenue) + 3}",
                expense_breakdown.values.tolist(),
            )
            logger.info("Charts data updated in Google Sheet '%s'.", self.config.charts_sheet_name)
        else:
            charts_data_path = os.path.join(
                os.path.dirname(self.config.csv_path), "charts_data.xlsx"
            )
            with pd.ExcelWriter(charts_data_path) as writer:
                weekly_revenue.to_excel(writer, sheet_name="Weekly_Revenue", index=False)
                expense_breakdown.to_excel(writer, sheet_name="Expense_Breakdown", index=False)
            logger.info("Charts data stored at %s", charts_data_path)

        self._generate_charts(weekly_revenue, expense_breakdown)

    # ------------------------- Visualization ----------------------------------
    def _generate_charts(self, weekly_revenue: pd.DataFrame, expense_breakdown: pd.DataFrame) -> None:
        if weekly_revenue.empty and expense_breakdown.empty:
            logger.warning("Insufficient data to generate charts.")
            return

        revenue_chart_path = os.path.join(self.config.chart_output_dir, "weekly_revenue.png")
        expense_chart_path = os.path.join(
            self.config.chart_output_dir, "expense_breakdown.png"
        )

        if not weekly_revenue.empty:
            plt.figure(figsize=(10, 6))
            plt.plot(weekly_revenue["Week"], weekly_revenue["Revenue"], marker="o")
            plt.title("Weekly Revenue Trend")
            plt.xlabel("Week Ending")
            plt.ylabel("Revenue ($)")
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(revenue_chart_path)
            plt.close()
            logger.info("Saved weekly revenue chart to %s", revenue_chart_path)

        if not expense_breakdown.empty:
            plt.figure(figsize=(10, 6))
            plt.bar(expense_breakdown["Category"], expense_breakdown["Amount"], color="teal")
            plt.title("Expense Category Breakdown")
            plt.xlabel("Category")
            plt.ylabel("Amount ($)")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(expense_chart_path)
            plt.close()
            logger.info("Saved expense breakdown chart to %s", expense_chart_path)

    # ------------------------- Runner -----------------------------------------
    def run_once(self) -> None:
        transactions = self.fetch_transactions()
        metrics = self.calculate_metrics(transactions)
        self.append_summary(metrics)
        self.update_charts_data(metrics)

    def run_daily_schedule(self) -> None:
        if schedule is None:
            raise RuntimeError(
                "schedule package is not installed. Install it or use an external scheduler like cron."
            )
        logger.info("Scheduling daily job at %s", self.config.schedule_time)
        schedule.every().day.at(self.config.schedule_time).do(self.run_once)
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")


# --------------------------- CLI Interface ------------------------------------

def parse_args(args: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automated financial tracker")
    parser.add_argument(
        "--csv-path",
        default="data/daily_transactions.csv",
        help="Path to CSV file with transaction data.",
    )
    parser.add_argument(
        "--use-google-sheet",
        action="store_true",
        help="Enable Google Sheets integration (requires credentials).",
    )
    parser.add_argument(
        "--google-credentials-json",
        default=None,
        help="Path to Google service account credentials JSON file.",
    )
    parser.add_argument(
        "--spreadsheet-name",
        default=None,
        help="Name of Google Sheets spreadsheet to update.",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run the tracker once and exit (useful for cron jobs).",
    )
    parser.add_argument(
        "--schedule-time",
        default="06:00",
        help="Daily schedule time in HH:MM (24h) format when using scheduler.",
    )
    return parser.parse_args(args)


def main(cli_args: Optional[Iterable[str]] = None) -> None:
    args = parse_args(cli_args)

    config = TrackerConfig(
        csv_path=args.csv_path,
        use_google_sheet=args.use_google_sheet,
        google_credentials_json=args.google_credentials_json,
        spreadsheet_name=args.spreadsheet_name,
        schedule_time=args.schedule_time,
    )

    tracker = FinancialTracker(config)
    if args.run_once or not args.use_google_sheet:
        tracker.run_once()
    else:
        tracker.run_daily_schedule()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - ensure errors are logged clearly
        logger.exception("Financial tracker failed: %s", exc)
        sys.exit(1)
