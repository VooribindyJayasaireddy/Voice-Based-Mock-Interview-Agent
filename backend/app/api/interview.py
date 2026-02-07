from fastapi import APIRouter, UploadFile, HTTPException
from uuid import uuid4

from app.services.stt import speech_to_text
from app.services.evaluation import evaluate_answer
from app.services.tts import text_to_speech
from app.services.llm import call_llm

import json

router = APIRouter()

# In-memory session store (hackathon-safe)
SESSIONS = {}

# -------------------------------
# Question Generator (LLM)
# -------------------------------
async def generate_questions(role: str, count: int = 3):
    prompt = f"""
You are an interview agent.

Generate {count} interview questions for the role: {role}.

Rules:
- Questions must be suitable for a spoken interview
- Open-ended
- Increasing difficulty
- No numbering
- No explanations

Return ONLY a JSON array of strings, no markdown or extra text.
Example:
["Question 1", "Question 2", "Question 3"]
"""
    response = await call_llm(prompt)
    
    # Try to extract JSON from markdown code blocks or find JSON array
    try:
        import re
        # Remove markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        else:
            # Try to find JSON array in the response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
        
        return json.loads(response)
    except (json.JSONDecodeError, AttributeError) as e:
        # Fallback to default questions if JSON parsing fails
        print(f"JSON parsing error in question generation: {e}")
        print(f"LLM response: {response}")
        return [
            f"Tell me about your experience with {role} responsibilities.",
            f"What technical skills do you bring to the {role} position?",
            f"Describe a challenging project you've worked on."
        ]

# -------------------------------
# Start Interview
# -------------------------------
@router.post("/start")
async def start_interview(role: str):
    interview_id = str(uuid4())

    # Generate questions using ChatGPT
    questions = await generate_questions(role)

    # Initialize session
    SESSIONS[interview_id] = {
        "index": 0,
        "questions": questions,
        "answers": []
    }

    question = questions[0]
    audio = await text_to_speech(question)

    return {
        "interview_id": interview_id,
        "question": question,
        "audio_file": audio
    }

# -------------------------------
# Submit Answer
# -------------------------------
@router.post("/{interview_id}/answer")
async def submit_answer(interview_id: str, audio: UploadFile):
    if interview_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Invalid interview session")

    audio_bytes = await audio.read()
    transcript = await speech_to_text(audio_bytes)

    idx = SESSIONS[interview_id]["index"]
    questions = SESSIONS[interview_id]["questions"]

    if idx >= len(questions):
        raise HTTPException(status_code=400, detail="Interview already completed")

    question = questions[idx]

    evaluation = await evaluate_answer(question, transcript)

    SESSIONS[interview_id]["answers"].append({
        "question": question,
        "transcript": transcript,
        "evaluation": evaluation
    })

    SESSIONS[interview_id]["index"] += 1

    return {
        "transcript": transcript,
        "evaluation": evaluation
    }

# -------------------------------
# Next Question
# -------------------------------
@router.get("/{interview_id}/next")
async def next_question(interview_id: str):
    if interview_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Invalid interview session")

    idx = SESSIONS[interview_id]["index"]
    questions = SESSIONS[interview_id]["questions"]

    if idx >= len(questions):
        return {"status": "completed"}

    question = questions[idx]
    audio = await text_to_speech(question)

    return {
        "question": question,
        "audio_file": audio
    }

# -------------------------------
# Interview Summary
# -------------------------------
@router.get("/{interview_id}/summary")
async def summary(interview_id: str):
    if interview_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Invalid interview session")

    answers = SESSIONS[interview_id]["answers"]
    
    if not answers:
        return {
            "overall_feedback": "No answers recorded yet.",
            "strengths": "N/A",
            "improvements": "N/A"
        }
    
    # Build comprehensive interview context for LLM
    interview_context = "Interview Performance Analysis:\n\n"
    for i, qa in enumerate(answers, 1):
        interview_context += f"Question {i}: {qa['question']}\n"
        interview_context += f"Answer: {qa['transcript']}\n"
        interview_context += f"Evaluation: Relevance={qa['evaluation']['relevance']}/10, "
        interview_context += f"Clarity={qa['evaluation']['clarity']}/10, "
        interview_context += f"Correctness={qa['evaluation']['correctness']}/10\n"
        interview_context += f"Feedback: {qa['evaluation']['feedback']}\n\n"
    
    # Generate comprehensive summary using LLM
    summary_prompt = f"""
{interview_context}

Based on this complete interview performance, provide a comprehensive summary with:

1. Overall Feedback: A 2-3 sentence summary of the candidate's overall performance
2. Strengths: Key strengths demonstrated across all answers (2-3 specific points)
3. Areas for Improvement: Specific actionable suggestions for improvement (2-3 points)

Return ONLY valid JSON, no markdown or extra text:
{{"overall_feedback": "text", "strengths": "text", "improvements": "text"}}
"""
    
    result = await call_llm(summary_prompt)
    
    # Parse JSON response with error handling
    try:
        import re
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
        # Fallback to basic summary if JSON parsing fails
        print(f"JSON parsing error in summary: {e}")
        print(f"LLM response: {result}")
        
        avg_scores = {
            "relevance": sum(qa['evaluation']['relevance'] for qa in answers) / len(answers),
            "clarity": sum(qa['evaluation']['clarity'] for qa in answers) / len(answers),
            "correctness": sum(qa['evaluation']['correctness'] for qa in answers) / len(answers)
        }
        
        return {
            "overall_feedback": f"Completed {len(answers)} questions with average scores: Relevance {avg_scores['relevance']:.1f}/10, Clarity {avg_scores['clarity']:.1f}/10, Correctness {avg_scores['correctness']:.1f}/10",
            "strengths": "Demonstrated engagement throughout the interview",
            "improvements": "Continue practicing to improve scores across all evaluation criteria"
        }

