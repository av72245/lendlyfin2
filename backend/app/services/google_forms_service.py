"""
Google Forms Service
Handles webhook submissions from Google Forms
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import hmac


class GoogleFormsService:
    """Service to handle Google Forms webhook submissions"""

    def __init__(self, webhook_secret: str = ""):
        """
        Initialize Google Forms service

        Args:
            webhook_secret: Secret key for webhook validation
        """
        self.webhook_secret = webhook_secret

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature (optional security measure)

        Args:
            payload: Request body bytes
            signature: Signature header value

        Returns:
            True if signature is valid
        """
        if not self.webhook_secret or not signature:
            return True  # Skip verification if no secret configured

        expected_sig = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_sig)

    def parse_google_form_submission(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Google Forms submission into standardized lead format

        Google Forms sends data in format:
        {
            "entry.123456789": "value",
            "entry.987654321": "value",
            ...
        }

        This method maps entry IDs to our schema.

        Args:
            form_data: Raw form data from Google Forms

        Returns:
            Standardized lead dictionary
        """
        # This mapping should be customized based on your Google Form entry IDs
        # You'll find these in the Google Form's pre-filled link or form HTML
        entry_mapping = {
            # "entry.XXXXXXXXX": "first_name",
            # "entry.YYYYYYYYY": "last_name",
            # etc.
        }

        # Split full name into first/last
        full_name = form_data.get('entry.1426650200', '')
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        lead = {
            'first_name': first_name,
            'last_name': last_name,
            'email': form_data.get('entry.1625657728', ''),
            'phone': form_data.get('entry.1862046678', ''),
            'loan_amount': form_data.get('entry.655443205', 0),
            'loan_purpose': form_data.get('entry.2095908657', ''),
            'property_type': form_data.get('entry.1322805430', ''),
            'credit_score': form_data.get('entry.1750047089', ''),
            'employment_status': form_data.get('entry.498771700', ''),
            'additional_notes': form_data.get('entry.28269328', ''),
            'submission_date': datetime.utcnow().isoformat(),
        }

        return lead

    def format_lead_for_email(self, lead: Dict[str, Any]) -> str:
        """
        Format lead data for email notification

        Args:
            lead: Standardized lead dictionary

        Returns:
            Formatted HTML string for email
        """
        html = f"""
        <h2>New Lead Submission</h2>
        <p><strong>Name:</strong> {lead.get('first_name', '')} {lead.get('last_name', '')}</p>
        <p><strong>Email:</strong> {lead.get('email', '')}</p>
        <p><strong>Phone:</strong> {lead.get('phone', '')}</p>
        <p><strong>Loan Amount:</strong> ${lead.get('loan_amount', 0):,.0f}</p>
        <p><strong>Loan Purpose:</strong> {lead.get('loan_purpose', '')}</p>
        <p><strong>Property Type:</strong> {lead.get('property_type', '')}</p>
        <p><strong>Credit Score:</strong> {lead.get('credit_score', '')}</p>
        <p><strong>Employment Status:</strong> {lead.get('employment_status', '')}</p>
        <p><strong>Additional Notes:</strong></p>
        <p>{lead.get('additional_notes', '')}</p>
        <p><small>Submitted: {lead.get('submission_date', '')}</small></p>
        """
        return html

    def extract_form_entries(self, form_response: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract entry IDs from Google Form response

        Call this to print out available entry IDs so you can map them above

        Args:
            form_response: Raw response from Google Forms

        Returns:
            Dictionary of entry IDs and their values
        """
        entries = {}
        for key, value in form_response.items():
            if key.startswith('entry.'):
                entries[key] = value
        return entries
