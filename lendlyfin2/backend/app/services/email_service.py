"""
Email service — sends notifications via SendGrid.
Falls back to console logging if no API key is set (dev mode).
"""
import json
import logging
from typing import Optional
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _send_via_sendgrid(to: str, subject: str, html: str) -> bool:
    """Send email via SendGrid HTTP API."""
    try:
        import urllib.request
        payload = json.dumps({
            "personalizations": [{"to": [{"email": to}]}],
            "from": {
                "email": settings.EMAIL_FROM,
                "name": settings.EMAIL_FROM_NAME
            },
            "subject": subject,
            "content": [{"type": "text/html", "value": html}]
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=payload,
            headers={
                "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            return resp.status == 202
    except Exception as e:
        logger.error(f"SendGrid error: {e}")
        return False


def send_email(to: str, subject: str, html: str) -> bool:
    """Send an email. Dev mode prints to console instead."""
    if not settings.SENDGRID_API_KEY or settings.APP_ENV == "development":
        logger.info(f"\n{'='*60}\nDEV EMAIL\nTo: {to}\nSubject: {subject}\n{'='*60}")
        return True
    return _send_via_sendgrid(to, subject, html)


# ── EMAIL TEMPLATES ───────────────────────────────────────────

def _base_template(content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }}
        .wrapper {{ max-width: 600px; margin: 32px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
        .header {{ background: #080D1A; padding: 28px 36px; }}
        .logo {{ font-size: 22px; font-weight: 700; color: #fff; letter-spacing: -1px; }}
        .logo em {{ color: #00E5A0; font-style: italic; }}
        .body {{ padding: 32px 36px; }}
        .label {{ font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
        .value {{ font-size: 16px; color: #1a1a1a; margin-bottom: 20px; }}
        .tag {{ display: inline-block; background: #e8faf3; color: #00875A; font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 6px; margin: 2px; }}
        .big {{ font-size: 32px; font-weight: 700; color: #00875A; }}
        .cta {{ display: inline-block; background: #00E5A0; color: #080D1A; font-size: 15px; font-weight: 700; padding: 14px 28px; border-radius: 10px; text-decoration: none; margin-top: 8px; }}
        .divider {{ height: 1px; background: #eee; margin: 24px 0; }}
        .footer {{ background: #f9f9f9; padding: 20px 36px; font-size: 12px; color: #999; border-top: 1px solid #eee; }}
        .urgent {{ background: #FFF3CD; border-left: 4px solid #FFA500; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px; font-size: 14px; }}
        h2 {{ font-size: 22px; color: #1a1a1a; margin: 0 0 20px; }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="header">
          <div class="logo">lendly<em>fin</em></div>
        </div>
        <div class="body">{content}</div>
        <div class="footer">
          © 2025 Lendlyfin Pty Ltd · ACL 000000 · <a href="https://lendlyfin.com.au" style="color:#00875A">lendlyfin.com.au</a>
        </div>
      </div>
    </body>
    </html>
    """


def send_new_lead_notification(lead) -> bool:
    """Notify broker immediately when a new lead is submitted."""
    interests = ""
    if lead.interests:
        try:
            items = json.loads(lead.interests)
            interests = "".join(f'<span class="tag">{i}</span>' for i in items)
        except Exception:
            interests = lead.interests

    # Build estimated borrowing power block
    bp_html = ""
    if lead.estimated_bp:
        bp_html = f"""
        <div class="label">Estimated Borrowing Power (calculator)</div>
        <div class="big">${lead.estimated_bp:,.0f}</div>
        <div class="divider"></div>
        """

    # Build income breakdown block if any income data was captured
    income_html = ""
    if lead.annual_income:
        overtime_str     = f"${lead.overtime:,.0f}"     if lead.overtime          else "—"
        bonus_str        = f"${lead.bonus:,.0f}"        if lead.bonus             else "—"
        partner_str      = f"${lead.partner_income:,.0f}" if lead.partner_income  else "—"
        expenses_str     = f"${lead.monthly_expenses:,.0f}/mo" if lead.monthly_expenses else "—"
        debts_str        = f"${lead.existing_debts:,.0f}/mo"   if lead.existing_debts   else "—"
        cc_str           = f"${lead.credit_card_limit:,.0f} limit" if lead.credit_card_limit else "—"
        dep_str          = str(lead.dependants) if lead.dependants is not None else "—"
        relationship_str = (lead.relationship or "—").title()

        income_html = f"""
        <div class="divider"></div>
        <h3 style="font-size:16px;color:#1a1a1a;margin:0 0 16px">📊 Financial Snapshot (from calculator)</h3>
        <table style="width:100%;border-collapse:collapse;font-size:14px">
          <tr style="background:#f9f9f9">
            <td style="padding:8px 12px;color:#666;width:50%">Base annual income</td>
            <td style="padding:8px 12px;font-weight:600">${lead.annual_income:,.0f}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;color:#666">Overtime (annual avg)</td>
            <td style="padding:8px 12px;font-weight:600">{overtime_str}</td>
          </tr>
          <tr style="background:#f9f9f9">
            <td style="padding:8px 12px;color:#666">Bonus / Commission</td>
            <td style="padding:8px 12px;font-weight:600">{bonus_str}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;color:#666">Partner income</td>
            <td style="padding:8px 12px;font-weight:600">{partner_str}</td>
          </tr>
          <tr style="background:#f9f9f9">
            <td style="padding:8px 12px;color:#666">Monthly expenses</td>
            <td style="padding:8px 12px;font-weight:600">{expenses_str}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;color:#666">Existing debts</td>
            <td style="padding:8px 12px;font-weight:600">{debts_str}</td>
          </tr>
          <tr style="background:#f9f9f9">
            <td style="padding:8px 12px;color:#666">Credit card limit</td>
            <td style="padding:8px 12px;font-weight:600">{cc_str}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;color:#666">Dependants</td>
            <td style="padding:8px 12px;font-weight:600">{dep_str}</td>
          </tr>
          <tr style="background:#f9f9f9">
            <td style="padding:8px 12px;color:#666">Relationship</td>
            <td style="padding:8px 12px;font-weight:600">{relationship_str}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;color:#666">Employment type</td>
            <td style="padding:8px 12px;font-weight:600">{lead.employment_type or '—'}</td>
          </tr>
          <tr style="background:#f9f9f9">
            <td style="padding:8px 12px;color:#666">Loan purpose</td>
            <td style="padding:8px 12px;font-weight:600">{lead.loan_purpose or '—'}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;color:#666">Deposit available</td>
            <td style="padding:8px 12px;font-weight:600">{'$' + f'{lead.deposit:,.0f}' if lead.deposit else '—'}</td>
          </tr>
        </table>
        """

    content = f"""
    <h2>🔔 New Lead — Action Required</h2>
    <div class="urgent">⚡ Speed matters — leads contacted within 1 hour convert 7× more often.</div>

    <div class="label">Name</div>
    <div class="value"><strong>{lead.first_name} {lead.last_name}</strong></div>

    <div class="label">Email</div>
    <div class="value"><a href="mailto:{lead.email}" style="color:#00875A">{lead.email}</a></div>

    <div class="label">Phone</div>
    <div class="value">{lead.phone or 'Not provided'}</div>

    <div class="label">Enquiry Type</div>
    <div class="value"><span class="tag">{lead.enquiry_type.value.replace('-', ' ').title()}</span></div>

    <div class="label">Budget Range</div>
    <div class="value">{lead.budget or 'Not specified'}</div>

    <div class="label">Preferred Contact Time</div>
    <div class="value">{lead.preferred_time or 'Anytime'}</div>

    {bp_html}

    <div class="label">Interests</div>
    <div class="value">{interests or 'None selected'}</div>

    <div class="label">Message</div>
    <div class="value" style="background:#f9f9f9;padding:14px;border-radius:8px;font-size:14px;line-height:1.6">{lead.message}</div>

    {income_html}

    <div class="divider"></div>
    <a href="https://lendlyfin.com.au/admin/leads/{lead.id}" class="cta">View Lead in Dashboard →</a>
    """
    return send_email(
        to=settings.BROKER_NOTIFICATION_EMAIL,
        subject=f"🔔 New Lead: {lead.first_name} {lead.last_name} — {lead.enquiry_type.value.replace('-',' ').title()}",
        html=_base_template(content),
    )


def send_lead_confirmation(lead) -> bool:
    """Confirm receipt to the person who submitted the form."""
    content = f"""
    <h2>We've received your enquiry, {lead.first_name}!</h2>

    <p style="color:#555;font-size:15px;line-height:1.7;margin-bottom:24px">
      Thanks for reaching out. Our mortgage broker will review your details and get back to you
      within <strong>one business day</strong> — by email, or by phone at your preferred time.
    </p>

    <div class="label">Your enquiry</div>
    <div class="value">{lead.enquiry_type.value.replace('-', ' ').title()}</div>

    <div class="label">Reference number</div>
    <div class="value" style="font-size:20px;font-weight:700;color:#00875A">#{lead.id:04d}</div>

    <div class="divider"></div>

    <p style="color:#555;font-size:14px;line-height:1.6">
      While you wait, you can use our free tools to explore further:<br><br>
      → <a href="https://lendlyfin.com.au/borrowing-power.html" style="color:#00875A">Check your borrowing power</a><br>
      → <a href="https://lendlyfin.com.au/compare-loans.html" style="color:#00875A">Compare home loan rates</a><br>
      → <a href="https://lendlyfin.com.au/repayments.html" style="color:#00875A">Calculate repayments</a>
    </p>

    <div class="divider"></div>
    <p style="color:#999;font-size:12px">
      If you have any urgent questions, email us at
      <a href="mailto:hello@lendlyfin.com.au" style="color:#00875A">hello@lendlyfin.com.au</a>
      or call <strong>1800 LENDLYFIN</strong>.
    </p>
    """
    return send_email(
        to=lead.email,
        subject="We've received your enquiry — Lendlyfin",
        html=_base_template(content),
    )


def send_status_update_email(lead, new_status: str) -> bool:
    """Notify lead when their status changes (e.g. qualified, won)."""
    messages = {
        "contacted":  ("We're on it!", "Our broker has reviewed your details and will be in touch very soon."),
        "qualified":  ("Great news!", "Based on your details, you look well-positioned to get approved. Our broker will be in touch to discuss your options."),
        "won":        ("Congratulations!", "Your home loan application has been successfully lodged. Our broker will keep you updated throughout the process."),
    }
    if new_status not in messages:
        return False

    heading, body = messages[new_status]
    content = f"""
    <h2>{heading} {lead.first_name}</h2>
    <p style="color:#555;font-size:15px;line-height:1.7">{body}</p>
    <div class="divider"></div>
    <div class="label">Reference</div>
    <div class="value" style="font-size:20px;font-weight:700;color:#00875A">#{lead.id:04d}</div>
    """
    return send_email(
        to=lead.email,
        subject=f"{heading} — Lendlyfin Update",
        html=_base_template(content),
    )
