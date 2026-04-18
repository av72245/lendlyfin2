"""
Google Sheets Service
Handles all interactions with Google Sheets for rates and criteria
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

# Scopes for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class GoogleSheetsService:
    """Service to fetch data from Google Sheets"""

    def __init__(self, credentials_json: str, sheet_id: str):
        """
        Initialize Google Sheets service

        Args:
            credentials_json: Path to or content of Google service account JSON
            sheet_id: Google Sheets document ID
        """
        self.sheet_id = sheet_id
        self.client = self._authenticate(credentials_json)
        self.spreadsheet = None
        self.rates_cache = None
        self.cache_time = None
        self.cache_ttl = 3600  # 1 hour cache

    def _authenticate(self, credentials_json: str):
        """Authenticate with Google API"""
        try:
            # If it looks like a file path, read it; otherwise treat as JSON string
            if os.path.exists(credentials_json):
                creds_dict = json.load(open(credentials_json))
            else:
                creds_dict = json.loads(credentials_json)

            creds = Credentials.from_service_account_info(
                creds_dict,
                scopes=SCOPES
            )
            return gspread.auth.Client(auth=creds)
        except Exception as e:
            print(f"Google Sheets authentication failed: {e}")
            return None

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self.rates_cache is None or self.cache_time is None:
            return False
        age = (datetime.utcnow() - self.cache_time).total_seconds()
        return age < self.cache_ttl

    def get_spreadsheet(self):
        """Get spreadsheet object (lazy load)"""
        if self.spreadsheet is None and self.client:
            try:
                self.spreadsheet = self.client.open_by_key(self.sheet_id)
            except Exception as e:
                print(f"Error opening spreadsheet: {e}")
        return self.spreadsheet

    def get_rates(self) -> List[Dict[str, Any]]:
        """
        Fetch loan products/rates from Google Sheets
        Expected sheet: "Loan Products"

        Columns:
        A: Product Name
        B: Interest Rate (%)
        C: Comparison Rate (%)
        D: Minimum Loan Amount
        E: Maximum Loan Amount
        F: Lender
        G: Active (TRUE/FALSE)

        Returns:
            List of rate dictionaries
        """
        # Check cache first
        if self._is_cache_valid() and self.rates_cache:
            return self.rates_cache

        rates = []
        try:
            spreadsheet = self.get_spreadsheet()
            if not spreadsheet:
                return []

            worksheet = spreadsheet.worksheet("Loan Products")
            rows = worksheet.get_all_records()

            for row in rows:
                if row.get('Active') in ['TRUE', True, 'true', 'Yes', 'yes']:
                    rate_obj = {
                        'product_name': row.get('Product Name', ''),
                        'min_rate': float(row.get('Interest Rate (%)', 0) or 0),
                        'comp_rate': float(row.get('Comparison Rate (%)', 0) or 0),
                        'min_loan': float(row.get('Minimum Loan Amount', 0) or 0),
                        'max_loan': float(row.get('Maximum Loan Amount', 0) or 0),
                        'lender': row.get('Lender', ''),
                    }
                    rates.append(rate_obj)

            # Update cache
            self.rates_cache = rates
            self.cache_time = datetime.utcnow()

        except Exception as e:
            print(f"Error fetching rates from Google Sheets: {e}")
            # Return cache even if expired in case of error
            if self.rates_cache:
                return self.rates_cache

        return rates

    def get_eligibility_criteria(self) -> Dict[str, Any]:
        """
        Fetch eligibility criteria from Google Sheets
        Expected sheet: "Eligibility Criteria"

        Returns:
            Dictionary of criteria
        """
        criteria = {}
        try:
            spreadsheet = self.get_spreadsheet()
            if not spreadsheet:
                return {}

            worksheet = spreadsheet.worksheet("Eligibility Criteria")
            rows = worksheet.get_all_records()

            for row in rows:
                name = row.get('Criteria Name', '')
                if name:
                    criteria[name] = {
                        'min': row.get('Min Value'),
                        'max': row.get('Max Value'),
                        'description': row.get('Description', '')
                    }

        except Exception as e:
            print(f"Error fetching eligibility criteria: {e}")

        return criteria

    def invalidate_cache(self):
        """Force cache invalidation"""
        self.rates_cache = None
        self.cache_time = None


# Global instance (will be initialized in main.py or config)
_sheets_service: Optional[GoogleSheetsService] = None


def get_sheets_service() -> Optional[GoogleSheetsService]:
    """Get global sheets service instance"""
    global _sheets_service
    return _sheets_service


def init_sheets_service(credentials_json: str, sheet_id: str):
    """Initialize global sheets service"""
    global _sheets_service
    _sheets_service = GoogleSheetsService(credentials_json, sheet_id)
