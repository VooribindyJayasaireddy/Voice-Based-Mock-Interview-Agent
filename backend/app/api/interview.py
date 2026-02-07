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
async def generate_questions(role: str, count: int = 3, candidate_name: str = None):
    # Add personalization if name is provided
    personalization = f"Address the candidate as {candidate_name} in the questions naturally." if candidate_name else ""
    
    prompt = f"""
You are an interview agent.

Generate {count} interview questions for the role: {role}.
{personalization}

Rules:
- Questions must be suitable for a spoken interview
- Open-ended
- Increasing difficulty
- No numbering
- No explanations
{"- Naturally incorporate the candidate's name in questions when appropriate" if candidate_name else ""}

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
        name_prefix = f"{candidate_name}, " if candidate_name else ""
        return [
            f"{name_prefix}Tell me about your experience with {role} responsibilities.",
            f"{name_prefix}What technical skills do you bring to the {role} position?",
            f"Describe a challenging project you've worked on."
        ]

# -------------------------------
# Start Interview
# -------------------------------
@router.post("/start")
async def start_interview(role: str):
    interview_id = str(uuid4())

    # Initialize session with name collection phase
    SESSIONS[interview_id] = {
        "role": role,
        "index": 0,
        "questions": [],
        "answers": [],
        "awaiting_name": True,
        "candidate_name": None
    }

    # Ask for name first
    name_question = "Hello! Before we begin the interview, could you please tell me your name?"
    audio = await text_to_speech(name_question)

    return {
        "interview_id": interview_id,
        "question": name_question,
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

    session = SESSIONS[interview_id]
    
    # Check if we're waiting for the candidate's name
    if session["awaiting_name"]:
        # Extract name from transcript
        candidate_name = transcript.strip()
        session["candidate_name"] = candidate_name
        session["awaiting_name"] = False
        
        # Generate personalized questions
        role = session["role"]
        questions = await generate_questions(role, count=3, candidate_name=candidate_name)
        session["questions"] = questions
        
        # Return first question with greeting
        first_question = f"Thank you, {candidate_name}! {questions[0]}"
        audio_file = await text_to_speech(first_question)
        
        return {
            "transcript": transcript,
            "evaluation": None,
            "next_question": first_question,
            "audio_file": audio_file,
            "name_collected": True
        }
    
    # Normal answer evaluation flow
    idx = session["index"]
    questions = session["questions"]

    if idx >= len(questions):
        raise HTTPException(status_code=400, detail="Interview already completed")

    question = questions[idx]
    candidate_name = session.get("candidate_name")

    evaluation = await evaluate_answer(question, transcript, candidate_name)

    session["answers"].append({
        "question": question,
        "transcript": transcript,
        "evaluation": evaluation
    })

    session["index"] += 1

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
    candidate_name = SESSIONS[interview_id].get("candidate_name", "the candidate")
    interview_context = f"Candidate Name: {candidate_name}\n\nInterview Performance Analysis:\n\n"
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

1. Overall Feedback: A 2-3 sentence summary of {candidate_name}'s overall performance
2. Strengths: Key strengths demonstrated across all answers (2-3 specific points)
3. Areas for Improvement: Specific actionable suggestions for improvement (2-3 points)

Address {candidate_name} directly in the feedback.

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

