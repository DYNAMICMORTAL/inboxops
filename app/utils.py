import re

def is_order_email(subject: str, body: str) -> bool:
    order_keywords = ['order', 'purchase', 'new order']
    return any(keyword in subject.lower() for keyword in order_keywords)

def extract_order_details(body: str) -> dict:
    # This is mock logic, you can replace with OpenAI LLM later
    # For now, extract product and quantity using simple pattern
    match = re.search(r"Product: (.*?), Quantity: (\d+)", body)
    if match:
        product = match.group(1).strip()
        quantity = int(match.group(2).strip())
        return {
            "product": product,
            "quantity": quantity,
            "customer": "Unknown"  # Can improve with LLM later
        }
    return None


import os
import google.generativeai as genai

# Directly set your Gemini API key here (replace with your actual key)
api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyB6SX989AFFnpD__XOi2Zcrg1RFPy35BsA")
genai.configure(api_key=api_key)

def is_order_email(subject: str, body: str) -> bool:
    keywords = ['order', 'purchase', 'new order']
    return any(k in subject.lower() for k in keywords)

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
    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
    try:
        response = await model.generate_content_async(prompt)
        if response.text:
            return response.text.strip()
        else:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                return f"Summarization failed: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}"
            return "Summarization failed: No content generated."
    except Exception as e:
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
    return "approval" in subject.lower() or "approve" in body.lower()

def extract_approval_details(body: str):
    # Basic rule-based extraction
    approval_type = "Leave" if "leave" in body.lower() else "General"
    return {
        "approval_type": approval_type,
        "request_text": body.strip()
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
    elif email.type in ["ORDER", "APPROVAL"]:
        return EmailStatus.AWAITING_APPROVAL
    
    # Default status for unclassified emails
    return EmailStatus.AWAITING