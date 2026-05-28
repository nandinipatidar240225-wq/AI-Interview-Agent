import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class EvaluationResult(BaseModel):
    score: float = Field(description="Overall score for the candidate's answer, out of 10.0 (e.g. 7.5)")
    strengths: list[str] = Field(description="List of strengths, key details, or correct points in the answer")
    weaknesses: list[str] = Field(description="List of weaknesses, omissions, or incorrect details in the answer")
    feedback: str = Field(description="Constructive and actionable feedback explaining how the candidate can improve their response")

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

def evaluate_answer(question, answer, api_key=None) -> EvaluationResult:
    client = get_client(api_key)

    prompt = f"""
    You are an expert technical interviewer evaluating a candidate's answer.

    Interview Question:
    {question}

    Candidate Answer:
    {answer}

    Analyze the candidate's response and evaluate their performance based on accuracy, completeness, and depth of technical understanding.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EvaluationResult,
        ),
    )

    try:
        result = EvaluationResult.model_validate_json(response.text)
        return result
    except Exception as e:
        return EvaluationResult(
            score=5.0,
            strengths=["Attempted the question"],
            weaknesses=["Unable to parse detailed feedback"],
            feedback=f"Raw evaluation response: {response.text}"
        )