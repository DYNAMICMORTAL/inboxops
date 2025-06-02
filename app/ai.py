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