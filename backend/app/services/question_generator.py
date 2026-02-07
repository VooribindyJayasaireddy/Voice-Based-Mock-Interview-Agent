from app.services.llm import call_llm
import json

async def generate_questions(role: str, count: int = 3):
    prompt = f"""
You are an interview agent.

Generate {count} interview questions for the role: {role}.
Questions should be:
- Clear
- Open-ended
- Suitable for a spoken interview

Return ONLY a JSON array of strings.
Example:
["Question 1", "Question 2"]
"""

    response = await call_llm(prompt)
    return json.loads(response)
