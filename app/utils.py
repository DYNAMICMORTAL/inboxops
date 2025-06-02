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