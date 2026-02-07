from app.services.llm import call_llm
import json
import re

async def evaluate_answer(question, answer):
    prompt = f"""
Question: {question}
Answer: {answer}

Evaluate from 0-10 on:
- Relevance
- Clarity
- Correctness

Return ONLY valid JSON, no markdown or extra text:
{{"relevance": int, "clarity": int, "correctness": int, "feedback": "text"}}
"""
    result = await call_llm(prompt)
    
    # Try to extract JSON from markdown code blocks or find JSON object
    try:
        # Remove markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        else:
            # Try to find JSON object in the response
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                result = json_match.group(0)
        
        return json.loads(result)
    except (json.JSONDecodeError, AttributeError) as e:
        # Fallback to default values if JSON parsing fails
        print(f"JSON parsing error: {e}")
        print(f"LLM response: {result}")
        return {
            "relevance": 5,
            "clarity": 5,
            "correctness": 5,
            "feedback": "Unable to evaluate answer properly. Please try again."
        }
