"""
Generic unbranded notification and reminder message templates.
Strictly complies with white-label requirements:
- No brand mentions (no ReMan).
- Opening greeting: "Greetings!"
- Sign-off: "Thank you,\nThe Management Team"
"""
import urllib.parse
from decimal import Decimal

def format_followup_reminder(name=None, related_to=None, reason=None, date=None, time=None, notes=None):
    greeting = "Greetings!"
    body_lines = []
    if name:
        body_lines.append(f"Dear {name},")
    body_lines.append("This is a reminder regarding your scheduled follow-up.")
    if related_to:
        body_lines.append(f"Regarding: {related_to}")
    if reason:
        body_lines.append(f"Purpose: {reason}")
    if date:
        date_str = date.strftime('%d/%m/%Y') if hasattr(date, 'strftime') else str(date)
        time_str = f" at {time.strftime('%I:%M %p')}" if time and hasattr(time, 'strftime') else (f" at {time}" if time else "")
        body_lines.append(f"Date & Time: {date_str}{time_str}")
    if notes:
        body_lines.append(f"Notes: {notes}")
    
    body = "\n".join(body_lines)
    signoff = "Thank you,\nThe Management Team"
    return f"{greeting}\n\n{body}\n\n{signoff}"

def format_payment_reminder(customer_name=None, site_number=None, balance=None, project_name=None, notes=None):
    greeting = "Greetings!"
    body_lines = []
    if customer_name:
        body_lines.append(f"Dear {customer_name},")
    body_lines.append("This is a reminder regarding your pending payment balance.")
    if site_number:
        proj_str = f" in {project_name}" if project_name else ""
        body_lines.append(f"Unit / Property: Site {site_number}{proj_str}")
    if balance is not None:
        bal_fmt = f"₹{balance:,.2f}" if isinstance(balance, (int, float, Decimal)) else f"₹{balance}"
        body_lines.append(f"Outstanding Balance: {bal_fmt}")
    if notes:
        body_lines.append(f"Details: {notes}")
    body_lines.append("Kindly process the pending balance at your earliest convenience.")
    
    body = "\n".join(body_lines)
    signoff = "Thank you,\nThe Management Team"
    return f"{greeting}\n\n{body}\n\n{signoff}"

def format_generic_alert(title, details=None):
    greeting = "Greetings!"
    body_lines = [title]
    if details:
        body_lines.append(details)
    body = "\n\n".join(body_lines)
    signoff = "Thank you,\nThe Management Team"
    return f"{greeting}\n\n{body}\n\n{signoff}"

def get_whatsapp_url(phone, message):
    if not phone:
        return ""
    clean_phone = "".join(filter(str.isdigit, str(phone)))
    # If standard 10 digit Indian number without country code, prepend 91
    if len(clean_phone) == 10:
        clean_phone = "91" + clean_phone
    encoded_text = urllib.parse.quote(message)
    return f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_text}"
