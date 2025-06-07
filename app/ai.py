import os
import asyncio
import google.generativeai as genai
try:
    api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyB6SX989AFFnpD__XOi2Zcrg1RFPy35BsA")
    # genai.configure(api_key=os.getenv("GOOGLE_API_KEY", "your-real-api-key-here"))
    if not api_key:
        print("Warning: GOOGLE_API_KEY environment variable not set. Consider setting it for better security.")
    else:
        genai.configure(api_key=api_key)

except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    print("Please ensure you have set the GOOGLE_API_KEY environment variable or configured the API key correctly.")
    exit()
async def generate_summary(text: str) -> str:
    """
    Generates a summary of the given text using the Gemini API.
    Args:
        text: The text content to summarize.
    Returns:
        The generated summary string, or an error message if summarization fails.
    """
    prompt = f"Please summarize the following email content concisely:\n\n---\n{text}\n---\n\nSummary:"
    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
    try:
        response = await model.generate_content_async(prompt)
        if response.text:
            summary = response.text.strip()
            return summary
        else:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                return f"Summarization failed due to: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}"
            return "Summarization failed: No content generated."
    except Exception as e:
        print(f"An error occurred during summary generation: {e}")
        return f"Error generating summary: {e}"
    
async def gemini_chat(messages: list[dict]) -> str:
    """
    messages: List of dicts like [{"role": "user", "parts": ["Hi"]}, ...]
    """
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyDPZJiV_pxYQxH_bzCAIcjbgfo2GdM3GSg"))
    model = genai.GenerativeModel("gemini-2.0-flash")
    chat = model.start_chat(history=messages[:-1])  # all but last as history
    response = chat.send_message(messages[-1]["parts"][0])
    return response.text


async def generate_auto_reply(email_json: dict) -> str:
    prompt = f"""
You are the InboxOps AI Assistant.
Your task is to read an incoming email (provided as a JSON object) and automatically generate a polished, accurate reply that resolves the sender’s request. Your reply must:

1. Greet the sender by name.
2. Reference any relevant identifiers (order numbers, ticket IDs, dates, etc.).
3. Acknowledge their question or issue.
4. Explain exactly what action you are taking or next steps.
5. Close with a friendly sign-off and the InboxOps support signature.

Always tailor tone and detail to the email’s context—formal for HR and approvals, empathetic for support, straightforward for orders or invoices. Do not mention that this is a simulation.

Email JSON:
{email_json}
"""
    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
    response = await model.generate_content_async(prompt)
    return response.text.strip() if response.text else "Thank you for your email. We'll get back to you soon.\n\n— InboxOps Support"