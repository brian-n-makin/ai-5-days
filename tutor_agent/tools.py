import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from tutor_agent.memory import StudentProfileManager

# Initialize the Gemini Client utilizing the corporate proxy base url
def get_gemini_client() -> genai.Client:
    base_url = os.environ.get("GOOGLE_GEMINI_BASE_URL")
    if not base_url:
        # Fallback to standard client if env var isn't present
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


def breakdown_topic(topic: str) -> List[str]:
    """Queries Gemini to subdivide a large topic into a sequential list of subjects.
    
    Args:
        topic: The high-level topic to learn (e.g. "Python Programming").
        
    Returns:
        A list of sub-topics/subjects.
    """
    client = get_gemini_client()
    prompt = f"Break down the topic '{topic}' into a logical, sequential list of 3 to 5 important sub-topics for learning."
    
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Curriculum,
                temperature=0.2,
            )
        )
        curriculum = Curriculum.model_validate_json(response.text)
        
        # Initialize student profile with these topics
        manager = StudentProfileManager()
        manager.initialize_profile(topic, curriculum.subjects)
        
        return curriculum.subjects
    except Exception as e:
        # Graceful fallback curriculum in case of API issues
        fallback = [f"Introduction to {topic}", f"Intermediate concepts in {topic}", f"Advanced {topic}"]
        manager = StudentProfileManager()
        manager.initialize_profile(topic, fallback)
        return fallback


def generate_quiz(subject: str, difficulty: str) -> Dict[str, Any]:
    """Generates a dynamic, high-quality multiple choice quiz question for a subject.
    
    Args:
        subject: The specific subject of the quiz.
        difficulty: The difficulty level (e.g., 'beginner', 'intermediate', 'advanced').
        
    Returns:
        A dict containing 'question', 'options', 'correct_option', and 'explanation'.
    """
    client = get_gemini_client()
    prompt = (
        f"Generate a single multiple-choice quiz question about '{subject}'.\n"
        f"The difficulty level is: {difficulty}.\n"
        f"Ensure there are exactly 4 distinct options."
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Quiz,
                temperature=0.7,
            )
        )
        quiz = Quiz.model_validate_json(response.text)
        return quiz.model_dump()
    except Exception as e:
        # Fallback quiz
        return {
            "question": f"What is a fundamental concept of {subject}?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_option": "Option A",
            "explanation": "This is a fallback explanation as the API failed."
        }


def assess_understanding(subject: str, correct: bool) -> Dict[str, Any]:
    """Evaluates user's quiz performance and updates their learning progress in memory.
    
    Args:
        subject: The subject that was tested.
        correct: True if the user answered correctly, False otherwise.
        
    Returns:
        A dictionary containing the updated subject progress details.
    """
    manager = StudentProfileManager()
    manager.load_profile()
    updated_subject = manager.update_subject_score(subject, correct)
    return updated_subject


def get_progress_summary() -> str:
    """Retrieves a friendly summary of the student's current curriculum and mastery levels.
    
    Returns:
        A formatted progress report string.
    """
    manager = StudentProfileManager()
    manager.load_profile()
    return manager.get_profile_summary()
