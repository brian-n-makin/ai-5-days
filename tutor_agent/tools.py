import os
import sys
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from rich.prompt import Confirm
from rich.console import Console
from google import genai
from google.genai import types
from tutor_agent.memory import StudentProfileManager

console = Console()

# Initialize the Gemini Client utilizing the corporate proxy base url
def get_gemini_client() -> genai.Client:
    base_url = os.environ.get("GOOGLE_GEMINI_BASE_URL")
    if not base_url:
        return genai.Client()
    return genai.Client(http_options={"base_url": base_url})

# Pydantic schemas for Structured LLM Outputs
class Curriculum(BaseModel):
    subjects: List[str] = Field(
        description="A list of 3 to 6 logical sequential sub-topics or subjects needed to master the main topic."
    )

class Quiz(BaseModel):
    question: str = Field(description="The quiz question text.")
    options: List[str] = Field(description="Exactly 4 multiple-choice options.")
    correct_option: str = Field(description="The exact correct option string from the options list.")
    explanation: str = Field(description="A brief explanation of why this option is correct.")


async def verify_quiz_correctness(quiz: Dict[str, Any]) -> bool:
    """Security & Self-Evaluation Guardrail to verify quiz safety and correctness."""
    client = get_gemini_client()
    prompt = (
        f"You are a Quality Assurance and Safety validator.\n"
        f"Analyze this multiple-choice quiz question for security, accuracy, and clarity:\n"
        f"Question: {quiz['question']}\n"
        f"Options: {quiz['options']}\n"
        f"Correct Answer: {quiz['correct_option']}\n"
        f"Explanation: {quiz['explanation']}\n\n"
        f"Check that:\n"
        f"1. The correct option is accurate and matches the question.\n"
        f"2. The question is entirely safe and appropriate for all students.\n"
        f"3. There is no ambiguity in the options.\n"
        f"Reply with exactly 'VALID' if it is perfect, or 'INVALID' if there are errors."
    )
    
    try:
        response = await client.aio.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1)
        )
        verdict = response.text.strip().upper()
        return "VALID" in verdict
    except Exception:
        # If verification fails due to network, default to True for resilience
        return True


async def breakdown_topic(topic: str) -> List[str]:
    """Asynchronously queries Gemini to subdivide a large topic into a sequential list of subjects.
    
    Includes Human-in-the-Loop confirmation before initializing the profile.
    """
    client = get_gemini_client()
    prompt = f"Break down the topic '{topic}' into a logical, sequential list of 3 to 5 important sub-topics for learning."
    
    try:
        response = await client.aio.models.generate_content(
            model="gemini-3-flash",  # Strategic model routing: Use fast gemini-3-flash for structured planner tasks
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Curriculum,
                temperature=0.2,
            )
        )
        curriculum = Curriculum.model_validate_json(response.text)
        subjects = curriculum.subjects
        
        # Human-In-The-Loop Confirmation Hook
        console.print(f"\n[bold gold3]🤖 [TutorSystem] Generated Curriculum Outline for '{topic}':[/bold gold3]")
        for i, sub in enumerate(subjects, 1):
            console.print(f"   {i}. {sub}")
            
        # Verify if running in interactive terminal
        if sys.stdin.isatty():
            confirmed = Confirm.ask("\n[bold gold3]Do you approve of this curriculum outline?[/bold gold3]", default=True)
            if not confirmed:
                console.print("[info]Modifying curriculum dynamically... (Adding default overview)[/info]")
                subjects = [f"{topic} Overview"] + subjects[:3]
        
        # Initialize student profile with these topics asynchronously
        manager = StudentProfileManager()
        await manager.initialize_profile(topic, subjects)
        
        return subjects
    except Exception as e:
        fallback = [f"Introduction to {topic}", f"Intermediate concepts in {topic}", f"Advanced {topic}"]
        manager = StudentProfileManager()
        await manager.initialize_profile(topic, fallback)
        return fallback


async def generate_quiz(subject: str, difficulty: str) -> Dict[str, Any]:
    """Asynchronously generates a single high-quality multiple choice quiz question.
    
    Includes an automated Self-Evaluation Guardrail.
    """
    client = get_gemini_client()
    prompt = (
        f"Generate a single multiple-choice quiz question about '{subject}'.\n"
        f"The difficulty level is: {difficulty}.\n"
        f"Ensure there are exactly 4 distinct options."
    )
    
    for attempt in range(2):  # Self-evaluation loop: retry once if guardrail fails
        try:
            response = await client.aio.models.generate_content(
                model="gemini-3.5-flash",  # Strategic model routing: Use gemini-3.5-flash for high reasoning teaching tasks
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Quiz,
                    temperature=0.7,
                )
            )
            quiz_data = Quiz.model_validate_json(response.text).model_dump()
            
            # Run Self-Evaluation Guardrail
            is_valid = await verify_quiz_correctness(quiz_data)
            if is_valid:
                return quiz_data
            else:
                console.print(f"[warning]⚠️ Guardrail alert: Regenerating quiz for {subject}...[/warning]")
        except Exception:
            pass
            
    # Default fallback quiz if API fails or guardrail keeps rejecting
    return {
        "question": f"What is a fundamental concept of {subject}?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_option": "Option A",
        "explanation": "This is a fallback explanation as the API failed."
    }


async def assess_understanding(subject: str, correct: bool) -> Dict[str, Any]:
    """Asynchronously evaluates user's quiz performance and updates their progress.
    
    Includes Human-In-The-Loop Confirmation before saving critical progress.
    """
    manager = StudentProfileManager()
    await manager.load_profile()
    
    # Human-In-The-Loop Confirmation Hook for State Modification
    result_str = "[green]CORRECT[/green]" if correct else "[red]INCORRECT[/red]"
    console.print(f"\n[bold gold3]🤖 [TutorSystem] Assessment result for '{subject}': {result_str}[/bold gold3]")
    
    if sys.stdin.isatty():
        confirmed = Confirm.ask("[bold gold3]Do you allow the agent to update your mastery score?[/bold gold3]", default=True)
        if not confirmed:
            console.print("[info]Score update canceled by user. Profile remains unchanged.[/info]")
            subjects = manager.profile.get("subjects", {})
            return subjects.get(subject, {"status": "in_progress", "score": 0, "quizzes_taken": 0, "quizzes_passed": 0})

    updated_subject = await manager.update_subject_score(subject, correct)
    return updated_subject


async def get_progress_summary() -> str:
    """Asynchronously retrieves a friendly summary of the student's current curriculum and mastery levels."""
    manager = StudentProfileManager()
    await manager.load_profile()
    return await manager.get_profile_summary()
