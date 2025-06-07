import re
from decimal import Decimal

def is_order_email(subject: str, body: str) -> bool:
    order_keywords = ['order', 'purchase', 'new order']
    return any(keyword in subject.lower() for keyword in order_keywords)

def extract_order_details(body: str) -> dict:
    match = re.search(r"Product: (.*?), Quantity: (\d+), USD\s*([\d,]+\.\d{2})", body)
    if match:
        product = match.group(1).strip()
        quantity = int(match.group(2).strip())
        total_value = Decimal(match.group(1).replace(",", ""))
        return {
            "product": product,
            "quantity": quantity,
            "customer": "Unknown",
            "total_value": total_value
        }
    return None


import os
import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyB6SX989AFFnpD__XOi2Zcrg1RFPy35BsA")
genai.configure(api_key=api_key)

def is_order_email(subject: str, body: str) -> bool:
    """
    Improved order email detection using more keywords and patterns.
    """
    order_keywords = [
        'order', 'purchase', 'new order', 'placed an order', 'buy', 'buying', 'bought',
        'invoice', 'payment received', 'your order', 'order confirmation',
        'order number', 'order id', 'order#', 'order #', 'transaction', 'receipt',
        'shipping', 'delivery', 'dispatched', 'fulfilled', 'processing order',
        'thank you for your order', 'your items', 'your products', 'your purchase'
    ]
    # Regex for order/invoice numbers (e.g., Order #12345, Invoice: 98765)
    patterns = [
        r'order[\s#:]*\d+', r'invoice[\s#:]*\d+', r'order id[\s#:]*\d+'
    ]
    text = f"{subject} {body}".lower()
    if any(keyword in text for keyword in order_keywords):
        return True
    for pat in patterns:
        if re.search(pat, text):
            return True
    return False

def extract_order_details(body: str) -> dict:
    match = re.search(r"Product: (.*?), Quantity: (\d+)", body)
    if match:
        return {
            "product": match.group(1).strip(),
            "quantity": int(match.group(2)),
            "customer": "Unknown"
        }
    return None

async def generate_order_summary(product: str, quantity: int) -> str:
    prompt = f"A customer placed an order for {quantity} units of {product}. Summarize this order in one sentence."
    print(f"Generating summary with prompt: {prompt}")
    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
    try:
        response = await model.generate_content_async(prompt)
        print(f"Response received: {response}")
        if response.text:
            return response.text.strip()
        else:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                return f"Summarization failed: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}"
            return "Summarization failed: No content generated."
    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"Error generating summary: {e}"
    

from postmarker.core import PostmarkClient

# Your server token from Postmark (Dashboard > Servers > API Tokens)
POSTMARK_TOKEN = "78a92885-74e3-42b0-8164-0b72fca59305"
FROM_EMAIL = "10bb06248998326c0167cda19c82da62@inbound.postmarkapp.com"

postmark = PostmarkClient(server_token=POSTMARK_TOKEN)

def send_order_confirmation_email(to_email: str, order_id: str, summary: str):
    try:
        response = postmark.emails.send(
            From=FROM_EMAIL,
            To=to_email,
            Subject=f"✅ Order {order_id} Confirmed!",
            HtmlBody=f"""
                <h2>Thank you for your order!</h2>
                <p><strong>Order ID:</strong> {order_id}</p>
                <p><strong>Summary:</strong><br>{summary}</p>
                <p>We'll process and ship your order soon. Stay tuned!</p>
                <br>
                <p>— InboxOps</p>
            """,
            TextBody=f"""
                Thank you for your order!

                Order ID: {order_id}
                Summary: {summary}

                We'll process and ship your order soon.

                — InboxOps
            """
        )
        print("✅ Email sent:", response)
    except Exception as e:
        print("❌ Failed to send confirmation email:", str(e))


def is_approval_email(subject: str, body: str) -> bool:
    """
    Improved approval email detection using more keywords and phrases.
    """
    approval_keywords = [
        'approval', 'approve', 'request approval', 'needs approval', 'pending approval',
        'please approve', 'seeking approval', 'awaiting approval', 'approved',
        'request for approval', 'approval needed', 'requires approval', 'grant approval',
        'manager approval', 'supervisor approval', 'access request', 'permission request'
    ]
    text = f"{subject} {body}".lower()
    return any(keyword in text for keyword in approval_keywords)

from datetime import datetime
import re

def extract_approval_details(body: str):
    # Extract dates in "YYYY-MM-DD" format
    date_pattern_iso = r"(\d{4}-\d{2}-\d{2})"
    dates_iso = re.findall(date_pattern_iso, body)

    # Extract dates in "Month Day, Year" format (e.g., June 10, 2025)
    date_pattern_text = r"([A-Za-z]+ \d{1,2}, \d{4})"
    dates_text = re.findall(date_pattern_text, body)

    start_date = None
    end_date = None

    # Parse ISO format dates
    if len(dates_iso) >= 2:
        start_date = datetime.strptime(dates_iso[0], "%Y-%m-%d")
        end_date = datetime.strptime(dates_iso[1], "%Y-%m-%d")
    # Parse text format dates
    elif len(dates_text) >= 2:
        start_date = datetime.strptime(dates_text[0], "%B %d, %Y")
        end_date = datetime.strptime(dates_text[1], "%B %d, %Y")

    print(f"Extracted Start Date: {start_date}, End Date: {end_date}")

    # Basic rule-based extraction
    approval_type = "Leave" if "leave" in body.lower() else "General"
    return {
        "approval_type": approval_type,
        "request_text": body.strip(),
        "start_date": start_date,
        "end_date": end_date,
    }



from datetime import datetime, timedelta
from .models import EmailStatus

def check_email_status(email) -> str:
    """
    Determine email status based on time and type
    Args:
        email: Email model instance
    Returns:
        str: Current status of the email
    """
    now = datetime.now(email.received_at.tzinfo)
    one_minute_ago = now - timedelta(minutes=1)
    
    # New emails (less than 1 minute old)
    if email.received_at > one_minute_ago:
        return EmailStatus.NEW
        
    # Type-based status for older emails
    if email.type == "SPAM":
        return EmailStatus.CLOSED
    elif email.type in ["ORDER", "APPROVAL", "SUPPORT_REQUEST"]:
        return EmailStatus.AWAITING_APPROVAL
    
    # Default status for unclassified emails
    return EmailStatus.AWAITING

from datetime import datetime

def format_date(value, format="%b %d, %I:%M %p"):
    """
    Custom Jinja2 filter to format dates.
    Args:
        value: The datetime object to format.
        format: The format string (default: "MMM d, h:mm A").
    Returns:
        str: The formatted date string.
    """
    if isinstance(value, datetime):
        return value.strftime(format)
    return value

import re

def extract_order_items(body: str) -> list:
    """
    Extract order items from the email body.
    Example format: "Item: Premium License, Quantity: 50, Price: $299"
    """
    item_pattern = r"Item:\s*(.*?),\s*Quantity:\s*(\d+),\s*Price:\s*\$([\d,]+\.\d{2})"
    matches = re.findall(item_pattern, body)
    items = []
    print("Raw email body for order extraction:", repr(body))
    for match in matches:
        items.append({
            "name": match[0].strip(),
            "quantity": int(match[1].strip()),
            "price": float(match[2].replace(",", "").strip()),
            "total": int(match[1].strip()) * float(match[2].replace(",", "").strip()),
            "category": "General"  # Default category, can be improved later
        })
    print(f"Extracted items: {items}")  # Debugging log
    return items

def extract_tags(body: str) -> list:
    """
    Extract tags from the email body.
    Example format: "Tags: enterprise, high-value, existing-customer, express-shipping"
    """
    inferred_tags = []
    tag_keywords = {
        "enterprise": ["enterprise", "corporate", "business", "organization", "company"],
        "high-value": ["expensive", "premium", "high-value", "luxury", "exclusive", "top-tier"],
        "existing-customer": ["existing customer", "repeat customer", "loyal customer", "returning customer"],
        "express-shipping": ["express shipping", "fast delivery", "priority shipping", "overnight shipping"],
        "bulk-order": ["bulk order", "large quantity", "wholesale", "high volume"],
        "discount": ["discount", "offer", "promotion", "sale", "deal", "special price"],
        "urgent": ["urgent", "asap", "immediate", "priority", "time-sensitive"],
        "international": ["international", "global", "overseas", "worldwide"],
        "subscription": ["subscription", "recurring", "membership", "renewal"],
        "new-customer": ["new customer", "first-time buyer", "new account"],
        "custom-order": ["custom order", "tailored", "bespoke", "personalized"],
        "payment-pending": ["payment pending", "awaiting payment", "unpaid", "invoice due"],
        "payment-confirmed": ["payment confirmed", "paid", "transaction complete", "payment received"],
        "refund": ["refund", "return", "money back", "reimbursement"],
        "cancellation": ["cancellation", "cancel order", "order canceled", "terminate"],
        "technical-support": ["technical support", "helpdesk", "issue", "problem", "troubleshooting"],
        "feedback": ["feedback", "review", "rating", "testimonial", "opinion"],
        "complaint": ["complaint", "issue", "problem", "dissatisfied", "unhappy"],
        "gift": ["gift", "present", "complimentary", "freebie"],
        "seasonal": ["seasonal", "holiday", "christmas", "black friday", "cyber monday", "new year"],
        "loyalty": ["loyalty", "reward", "points", "membership benefits"],
        "wholesale": ["wholesale", "bulk", "reseller", "distributor"],
        "shipping-delay": ["shipping delay", "late delivery", "delayed shipment"],
        "order-confirmation": ["order confirmation", "order received", "order placed"],
        "invoice": ["invoice", "billing", "payment details", "receipt"],
        "tracking": ["tracking", "shipment tracking", "delivery status", "tracking number"],
        "out-of-stock": ["out of stock", "unavailable", "backorder", "restock"],
        "pre-order": ["pre-order", "advance order", "coming soon"],
        "customer-service": ["customer service", "support", "help", "assistance"],
        "priority-customer": ["priority customer", "vip", "important client"],
        "order-update": ["order update", "status update", "order progress"],
        "product-query": ["product query", "product question", "product details"],
        "invoice-query": ["invoice query", "billing question", "payment inquiry"],
        "shipping-query": ["shipping query", "delivery question", "shipment inquiry"],
        "return-request": ["return request", "refund request", "exchange request"],
        "damaged-product": ["damaged product", "broken item", "defective item"],
        "replacement-request": ["replacement request", "exchange", "item replacement"],
        "order-error": ["order error", "wrong item", "incorrect order"],
        "thank-you": ["thank you", "appreciation", "gratitude", "thanks"],
        "new-product": ["new product", "latest release", "new arrival"],
        "promotion": ["promotion", "special offer", "limited time deal"],
        "subscription-renewal": ["subscription renewal", "membership renewal", "auto-renew"],
        "account-issue": ["account issue", "login problem", "account locked"],
        "password-reset": ["password reset", "forgot password", "reset link"],
        "order-correction": ["order correction", "update order", "modify order"],
        "customer-feedback": ["customer feedback", "survey", "opinion"],
        "high-priority": ["high priority", "urgent", "critical"],
        "low-stock": ["low stock", "limited availability", "almost gone"],
        "gift-card": ["gift card", "voucher", "e-gift"],
        "special-request": ["special request", "customization", "specific instructions"],
        "bulk-discount": ["bulk discount", "wholesale price", "volume pricing"],
        "order-followup": ["order follow-up", "order inquiry", "order status"],
        "delivery-confirmation": ["delivery confirmation", "item delivered", "received package"],
        "customer-query": ["customer query", "question", "inquiry"],
        "order-escalation": ["order escalation", "complaint escalation", "priority escalation"],
        "product-feedback": ["product feedback", "product review", "product rating"],
        "order-issue": ["order issue", "problem with order", "order complaint"],
        "shipping-issue": ["shipping issue", "delivery problem", "shipment delay"],
        "payment-issue": ["payment issue", "billing problem", "transaction error"],
        "order-history": ["order history", "past orders", "previous purchases"],
        "wishlist": ["wishlist", "saved items", "favorites"],
        "order-tracking": ["order tracking", "track shipment", "delivery tracking"],
        "customer-loyalty": ["customer loyalty", "reward program", "loyalty points"],
        "order-priority": ["order priority", "rush order", "expedited"],
        "order-status": ["order status", "current status", "order progress"],
        "customer-complaint": ["customer complaint", "negative feedback", "issue reported"],
        "order-confirmed": ["order confirmed", "confirmation received", "order accepted"],
        "order-pending": ["order pending", "awaiting confirmation", "processing"],
        "order-completed": ["order completed", "fulfilled", "shipped"],
        "order-canceled": ["order canceled", "cancellation confirmed", "order terminated"]
    }
    for tag, keywords in tag_keywords.items():
        if any(keyword in body.lower() for keyword in keywords):
            inferred_tags.append(tag)

    return inferred_tags

import re
# from app.ai import openai_call

def extract_customerMail_tags(text: str):
    keywords = re.findall(r'\b(refund|invoice|login|password|delay|urgent|crash|complaint)\b', text.lower())
    return list(set(keywords))

from .ai import generate_summary

def is_support_ticket(subject: str, body: str) -> bool:
    """Heuristically detect if an email is a customer support inquiry."""
    subject_lower = subject.lower()
    body_lower = body.lower()
    keywords = ["help", "support", "issue", "problem", "login", "error", "not working", "complaint", "ticket", "inquiry"]
    combined = f"{subject} {body}".lower()
    return any(word in subject_lower for word in keywords) or any(word in body_lower for word in keywords)


async def classify_criticality(text: str):
    prompt = f"Classify this support message's urgency (Low, Medium, High, Urgent):\n{text}\nRespond with only one word: Low, Medium, High, or Urgent."
    return await generate_summary(prompt)