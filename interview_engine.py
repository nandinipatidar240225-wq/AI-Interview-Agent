import os
from google import genai

def get_client(api_key=None):
    """
    Resolves the client using the provided API key, or falls back to
    environment variables (GEMINI_API_KEY or GOOGLE_API_KEY).
    """
    if api_key:
        return genai.Client(api_key=api_key)
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_key:
        return genai.Client(api_key=env_key)
    return genai.Client()

def generate_question(resume_text, api_key=None):
    client = get_client(api_key)

    prompt = f"""
    You are an expert AI Interviewer.

    Candidate Resume:
    {resume_text}

    Based on the candidate's resume, ask ONE challenging, relevant technical interview question that specifically tests their skills, projects, or education.
    Keep the question professional, clear, and context-specific. Do not include introductory conversational text, just ask the question directly.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text

